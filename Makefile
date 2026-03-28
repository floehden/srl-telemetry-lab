.PHONY: all kind clab setup-nodes cilium mesh clean

# Default target to run the entire pipeline
all: kind clab setup-nodes cilium mesh

kind:
	@echo "🚀 Spinning up Kind clusters..."
	kind create cluster --name c1 --config configs/cluster/kind-c1.yaml
	kind create cluster --name c2 --config configs/cluster/kind-c2.yaml
	kind create cluster --name c3 --config configs/cluster/kind-c3.yaml

clab:
	@echo "🕸️ Deploying Containerlab topology..."
	sudo clab deploy -t st.clab.yml --reconfigure

setup-nodes:
	@echo "🔌 Configuring eth1 IPs on Kind nodes..."
	# Assuming your script from the context is saved as setup-kind-ips.sh
	chmod +x setup-kind-ips.sh
	./setup-kind-ips.sh

cilium:
	@echo "🐝 Installing Cilium via CLI & Enabling Hubble..."
	cilium install --context kind-c1 --set cluster.name=c1 --set cluster.id=1
	cilium hubble enable --ui --context kind-c1
	
	cilium install --context kind-c2 --set cluster.name=c2 --set cluster.id=2
	cilium hubble enable --ui --context kind-c2
	
	cilium install --context kind-c3 --set cluster.name=c3 --set cluster.id=3
	cilium hubble enable --ui --context kind-c3

mesh:
	@echo "🌐 Enabling and connecting ClusterMesh..."
	# 1. Enable ClusterMesh control plane on all clusters
	cilium clustermesh enable --context kind-c1 --service-type NodePort
	cilium clustermesh enable --context kind-c2 --service-type NodePort
	cilium clustermesh enable --context kind-c3 --service-type NodePort
	
	@echo "⏳ Waiting for ClusterMesh to enable (sleeping for 30s)..."
	sleep 30
	
	# 2. Connect the clusters together
	cilium clustermesh connect --context kind-c1 --destination-context kind-c2 --allow-mismatching-ca
	cilium clustermesh connect --context kind-c1 --destination-context kind-c3 --allow-mismatching-ca
	cilium clustermesh connect --context kind-c2 --destination-context kind-c3 --allow-mismatching-ca

clean:
	@echo "🧹 Tearing down the lab..."
	sudo clab destroy -t st.clab.yml --cleanup
	kind delete cluster --name c1
	kind delete cluster --name c2
	kind delete cluster --name c3