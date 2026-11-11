# TODO: canary

Write three files here:

- `stable.yaml`: Deployment `menu-stable`, 9 replicas, label `app: menu`, APP_VERSION "1.0.0"
- `canary.yaml`: Deployment `menu-canary`, 1 replica, label `app: menu`, APP_VERSION "2.0.0"
- `service.yaml`: Service `menu` (port 8001) with the selector `app: menu` ONLY (no track label): it spreads traffic over all ten pods

The share of traffic the canary gets is the share of pods it has (here about 10%). Abort the canary by scaling it to 0.
