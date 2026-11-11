# TODO: blue/green

Write three files here:

- `blue.yaml`: Deployment `menu-blue`, 3 replicas, labels `app: menu` and `track: blue`, APP_VERSION "1.0.0"
- `green.yaml`: Deployment `menu-green`, 3 replicas, labels `app: menu` and `track: green`, APP_VERSION "2.0.0"
- `service.yaml`: Service `menu` (port 8001) whose selector is `app: menu` AND `track: blue`

Both versions run at the same time; only the Service decides who gets traffic. The switch is one patch of the selector.
