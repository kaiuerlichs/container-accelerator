from kubernetes import client as k8s_client


def create_namespaces(namespaces_to_create: list):
    v1 = k8s_client.CoreV1Api()
    existing_namespaces = [item.metadata.name for item in v1.list_namespace().items]
    
    for name in namespaces_to_create:
        if name in existing_namespaces:
            continue

        ns = k8s_client.V1Namespace(metadata=k8s_client.V1ObjectMeta(
            name=name, 
            labels={
                "name": name
            })
        )
        v1.create_namespace(ns)
