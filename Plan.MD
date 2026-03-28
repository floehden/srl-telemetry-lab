# Roadmap 

### Phase 1: IPAM & Network Design Strategy
Before writing any code, we need strict CIDR boundaries so the clusters can route to each other across your EVPN fabric without conflicts.

* **Cluster 1 (Attached to Leaf 1):**
    * Node Subnet: `172.17.1.0/24`
    * Pod CIDR: `10.10.0.0/16`
    * Service CIDR: `10.11.0.0/16`
* **Cluster 2 (Attached to Leaf 2):**
    * Node Subnet: `172.17.2.0/24`
    * Pod CIDR: `10.20.0.0/16`
    * Service CIDR: `10.21.0.0/16`
* **Cluster 3 (Attached to Leaf 3):**
    * Node Subnet: `172.17.3.0/24`
    * Pod CIDR: `10.30.0.0/16`
    * Service CIDR: `10.31.0.0/16`

### Phase 2: Update Containerlab Topology (`st.clab.yml`)
Since `kind` spins up standard Docker containers, we will deploy the `kind` clusters *first* on the host, and then use Containerlab to wire those existing `kind` containers directly to your SR Linux leafs alongside your existing clients.

* **Retain the old Linux clients:** Keep `client1`, `client2`, and `client3` wired to `e1-1` on their respective leafs.
* **Define Links to Kind Nodes:** Connect the SR Linux interfaces to the pre-provisioned `kind` containers using `ext-container` endpoints. 
    * *Example for Leaf 1:* Connect `leaf1:e1-1` to `client1`, `leaf1:e1-2` to `c1-control-plane`, `leaf1:e1-3` to `c1-worker`, etc.

### Phase 3: Update SR Linux Fabric Configs
Enable the additional downlinks on your leafs to accommodate both the existing clients and the new Kubernetes nodes.

* **Enable Additional Downlinks:** On each leaf, ensure `ethernet-1/1` through `ethernet-1/4` are enabled as bridged subinterfaces.
* **Assign to MAC-VRF:** Map all four interfaces to `network-instance vrf-1`. This places the legacy client and all three `kind` nodes of a specific cluster into the same L2 broadcast domain.
* **L3 Gateway (IRB):** Ensure the leafs can route between the node subnets (172.17.X.0/24) so the clusters can reach each other via the EVPN overlay.

### Phase 4: Cluster Provisioning (`kind`)
We will automate the creation of three highly specific `kind` configurations.

* **Disable Default CNI:** Cilium will handle networking, so the default Kindnet CNI must be disabled (`disableDefaultCNI: true`).
* **Set Custom CIDRs:** Inject the Pod and Service CIDRs defined in Phase 1 into the `kind` config files.

### Phase 5: Cilium, Hubble & ClusterMesh Deployment (CLI Approach)
Once the topology is up and the `kind` nodes are wired to the leafs, we will use the `cilium cli` to bootstrap the data plane and observability stack.

1.  **Install Cilium via CLI:** Deploy Cilium to all three clusters, explicitly setting the cluster name and ID (required for ClusterMesh).
    * `cilium install --context kind-c1 --cluster-name c1 --cluster-id 1`
    * `cilium install --context kind-c2 --cluster-name c2 --cluster-id 2`
    * `cilium install --context kind-c3 --cluster-name c3 --cluster-id 3`
2.  **Enable Hubble & UI:** Turn on the observability stack so we can visually trace cross-cluster traffic.
    * `cilium hubble enable --ui --context kind-c1` (Repeat for c2 and c3)
3.  **Enable ClusterMesh:** Turn on the ClusterMesh control plane on all clusters.
    * `cilium clustermesh enable --context kind-c1` (Repeat for c2 and c3)
4.  **Connect the Clusters:** Use the CLI to securely extract and distribute the CA certs and endpoints.
    * `cilium clustermesh connect --context kind-c1 --destination-context kind-c2`
    * `cilium clustermesh connect --context kind-c1 --destination-context kind-c3`
    * `cilium clustermesh connect --context kind-c2 --destination-context kind-c3`

### Phase 6: Automation Workflow (The "Makefile" Approach)
To make this reproducible, we will wrap this in a Makefile. The execution order is critical:

1.  **`make kind`**: Provisions the three `kind` clusters (Docker containers are created).
2.  **`make clab`**: Deploys the modified `st.clab.yml`, deploying the SR Linux fabric, telemetry stack, and dynamically connecting to the running `kind` containers and legacy clients.
3.  **`make setup-nodes`**: Configures the IP addresses on the `eth1` interfaces inside the `kind` containers so they can talk to the SR Linux leafs.
4.  **`make cilium`**: Executes the `cilium install` and `cilium hubble enable` commands across all contexts.
5.  **`make mesh`**: Executes the `cilium clustermesh enable` and `connect` commands to establish the multi-cluster routing.

---
