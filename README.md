# Nokia SR Linux & Cilium ClusterMesh Telemetry Lab

[![Discord][discord-svg]][discord-url] [![DevPod][devpod-svg]][devpod-url] [![Codespaces][codespaces-svg]][codespaces-url]  
![w212][w212][Learn more](https://containerlab.dev/macos/#devpod) ![w90][w90][Learn more](https://containerlab.dev/manual/codespaces)

[discord-svg]: https://gitlab.com/rdodin/pics/-/wikis/uploads/b822984bc95d77ba92d50109c66c7afe/join-discord-btn.svg
[discord-url]: https://discord.gg/tZvgjQ6PZf
[devpod-svg]: https://gitlab.com/rdodin/pics/-/wikis/uploads/dfc36636ecaa60f3e70340686d5800db/open-in-devpod-btn.svg
[devpod-url]: https://devpod.sh/open#https://github.com/srl-labs/srl-telemetry-lab
[codespaces-svg]: https://gitlab.com/rdodin/pics/-/wikis/uploads/80546a8c7cda8bb14aa799d26f55bd83/run-codespaces-btn.svg
[codespaces-url]: https://codespaces.new/srl-labs/srl-telemetry-lab?quickstart=1&devcontainer_path=.devcontainer%2Fdocker-in-docker%2Fdevcontainer.json
[w212]: https://gitlab.com/rdodin/pics/-/wikis/uploads/718a32dfa2b375cb07bcac50ae32964a/w212h1.svg
[w90]: https://gitlab.com/rdodin/pics/-/wikis/uploads/bf1b8ea28b4528eb1b66567355a13c5c/w90h1.svg
[Learn more](https://containerlab.dev/macos/#devpod) [Learn more](https://containerlab.dev/manual/codespaces)

This lab represents a hybrid infrastructure environment featuring a Clos fabric built with [Nokia SR Linux](https://learn.srlinux.dev/) running Layer 2 EVPN, seamlessly integrating **Legacy Linux Clients** and **Multi-Cluster Kubernetes (Kind)**. The Kubernetes clusters are interconnected using **Cilium ClusterMesh**, enabling cross-cluster pod-to-pod routing and Global Services directly over the EVPN overlay.

Additionally, SR Linux has first-class Streaming Telemetry support thanks to [100% YANG coverage](https://learn.srlinux.dev/yang/) of state and config data. The lab topology includes a comprehensive observability stack comprised of Hubble (for Cilium datapath visibility), gnmic, Prometheus, Grafana, Promtail, and Loki.

-----

### Goals of this lab:

1.  **Automated Infrastructure:** Use a Makefile to seamlessly provision Kind clusters, wire them to SR Linux via Containerlab, and bootstrap Cilium.
2.  **Multi-Cluster Networking:** Demonstrate Cilium ClusterMesh establishing VXLAN/Geneve tunnels between disparate Kubernetes clusters over an SR Linux L2 EVPN fabric.
3.  **Global Services:** Showcase cross-cluster load balancing using Cilium's `io.cilium/global-service` annotations.
4.  **Holistic Telemetry:** Provide practical configuration examples for the gnmic collector to export fabric metrics to a Prometheus TSDB.
5.  **Advanced Dashboarding:** Utilize the [FlowPlugin](https://grafana.com/grafana/plugins/andrewbmchugh-flow-panel/) for rendering port speeds, and introduce Loki/Promtail to consume Syslog data from the network nodes.

-----

## Prerequisites

Before deploying, ensure you have the following installed on your host:

  * [Docker](https://docs.docker.com/engine/install/)
  * [Containerlab](https://containerlab.dev/install/)
  * [Kind (Kubernetes IN Docker)](https://www.google.com/search?q=https://kind.sigs.k8s.io/docs/user/quick-start/%23installation)
  * [Cilium CLI](https://www.google.com/search?q=https://docs.cilium.io/en/stable/gettingstarted/k8s-install-default/%23install-the-cilium-cli)
  * `kubectl` and `make`

## Deploying the lab

The entire environment—including K8s provisioning, fabric wiring, and Cilium mesh establishment—is automated via the included `Makefile`.

```bash
# Clone the repository and change into the directory, then execute:
make all
```

**The `make all` pipeline executes the following phases in order:**

1.  `make kind`: Provisions three bare Kind clusters (`c1`, `c2`, `c3`) with custom pod/service CIDRs and default CNI disabled.
2.  `make clab`: Deploys the `st.clab.yml` Containerlab topology, spinning up the SR Linux fabric, Telemetry stacks, and dynamically attaching the Kind nodes to the leaf switches using `ext-container` links.
3.  `make setup-nodes`: Configures the IP addressing on the Kind worker nodes to communicate with the SR Linux MAC-VRFs.
4.  `make cilium`: Installs Cilium and enables Hubble observability across all three clusters using the CLI.
5.  `make mesh`: Enables the ClusterMesh apiservers (via NodePort) and mutually connects the clusters, merging the CA certificates to establish trust.

To tear down the entire lab:

```bash
make clean
```

-----

## Fabric & Kubernetes Configuration

The DC fabric consists of three leaves and two spines. Leaves and spines use Nokia SR Linux IXR-D2 and IXR-D3L chassis respectively. The underlay network runs eBGP, while iBGP is used for the overlay network.

Each Leaf switch maps its downlink interfaces to a `mac-vrf` (L2 broadcast domain). This allows the legacy `client` containers and the `kind` control-plane/worker nodes attached to that leaf to share a subnet and communicate natively. The EVPN overlay routes traffic *between* the leaves, enabling K8s nodes in Cluster 1 to reach K8s nodes in Cluster 2.

### Verifying the ClusterMesh Datapath

Once deployed, verify that Cilium has successfully established the multi-cluster mesh:

```bash
cilium clustermesh status --context kind-c1
```

*You should see `✅ All 3 nodes are connected to all clusters`.*

### Testing Cross-Cluster Global Services

To demonstrate Cilium's ability to load balance traffic across the EVPN fabric, we will deploy a "Global Service".

1.  **Deploy the Global Service Definition to all clusters:**
    ```bash
    kubectl apply -f testing/global-service.yaml --context kind-c1
    kubectl apply -f testing/global-service.yaml --context kind-c2
    kubectl apply -f testing/global-service.yaml --context kind-c3
    ```
2.  **Deploy the backend applications only to Cluster 2 and 3:**
    ```bash
    kubectl apply -f testing/backend-c2.yaml --context kind-c2
    kubectl apply -f testing/backend-c3.yaml --context kind-c3
    ```
3.  **Trigger traffic from Cluster 1:**
    Cluster 1 has no backends. We will deploy a tester pod in `c1` and curl the service. Cilium will intercept the traffic and tunnel it across the SR Linux fabric to `c2` and `c3`.
    ```bash
    kubectl run x-wing --image=curlimages/curl --context kind-c1 --restart=Never -- sleep 3600

    # Wait for the pod to be running, then execute the test:
    for i in {1..6}; do kubectl exec x-wing --context kind-c1 -- curl -s http://rebel-base; done
    ```
    *Expected Output: The responses will perfectly load-balance between `🚀 Greetings from Cluster 2!` and `🛸 Greetings from Cluster 3!`.*

-----

## Telemetry & Logging Stack

As the lab name suggests, telemetry is at its core. The following stack is used in this lab:

| Role                | Software                              |
| ------------------- | ------------------------------------- |
| Datapath Visibility | [Hubble](https://docs.cilium.io/en/stable/gettingstarted/hubble/) |
| Telemetry collector | [gnmic](https://gnmic.openconfig.net) |
| Time-Series DB      | [prometheus](https://prometheus.io)   |
| Visualization       | [grafana](https://grafana.com)        |
| Log Aggregation     | Loki & Promtail                       |

### Access details

Using containerlab's ability to expose ports of the containers to the host, the following services are available on the host machine:

  * **Grafana:** [http://localhost:3000](https://www.google.com/search?q=http://localhost:3000). Anonymous access is enabled. (Admin credentials: `admin/admin`).
  * **Prometheus:** [http://localhost:9090/graph](https://www.google.com/search?q=http://localhost:9090/graph)
  * **Hubble UI (per K8s cluster):** Run `cilium hubble ui --context kind-c1` to port-forward and open the real-time flow map in your browser.

### Grafana & FlowPlugin

Grafana is a key component of this lab as it provides the visualisation for the collected telemetry data. The Grafana dashboard provided by this repository provides multiple views on the collected real-time data. Powered by the [flow plugin](https://grafana.com/grafana/plugins/andrewbmchugh-flow-panel/) it overlays telemetry sourced data over graphics such as topology and front panel views:

Using the flow plugin and real telemetry data users can create interactive topology maps with a visual indication of link rate/utilization.

### Logging stack

The logging stack leverages the promtail-\>Loki pipeline. The logging infrastructure captures every message from SR Linux that is above the Info level. This includes all BGP messages, system messages, and interface state changes. The Grafana dashboard provides a view on the collected logs and allows filtering on a per-application level.
