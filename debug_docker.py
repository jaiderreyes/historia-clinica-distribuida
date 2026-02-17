import docker

client = docker.from_env()
print("Containers found by python client:")
for container in client.containers.list(all=True):
    print(f"Name: {container.name}, ID: {container.id}, Status: {container.status}")
