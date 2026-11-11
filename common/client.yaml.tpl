# PROVIDED. A pod inside the cluster that the checker (and you) use to send requests to the menu Service by name,
# so that the traffic is spread by Kubernetes exactly as real traffic would be (a port-forward would pin one pod).
apiVersion: apps/v1
kind: Deployment
metadata:
  name: client
  namespace: beanie-deploy
  labels: {app: client}
spec:
  replicas: 1
  selector:
    matchLabels: {app: client}
  template:
    metadata:
      labels: {app: client}
    spec:
      containers:
        - name: client
          image: __IMAGE__
          command: ["python", "-c", "import time; time.sleep(10**9)"]
          resources:
            requests: {cpu: 20m, memory: 48Mi}
            limits: {memory: 128Mi}
          securityContext:
            runAsNonRoot: true
            allowPrivilegeEscalation: false
