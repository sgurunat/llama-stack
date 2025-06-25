# Configuring a "Stack"

The Llama Stack runtime configuration is specified as a YAML file. Here is a simplified version of an example configuration file for the Ollama distribution:

```{dropdown} 👋 Click here for a Sample Configuration File

```yaml
version: 2
conda_env: ollama
apis:
- agents
- inference
- vector_io
- safety
- telemetry
providers:
  inference:
  - provider_id: ollama
    provider_type: remote::ollama
    config:
      url: ${env.OLLAMA_URL:http://localhost:11434}
  vector_io:
  - provider_id: faiss
    provider_type: inline::faiss
    config:
      kvstore:
        type: sqlite
        namespace: null
        db_path: ${env.SQLITE_STORE_DIR:~/.llama/distributions/ollama}/faiss_store.db
  safety:
  - provider_id: llama-guard
    provider_type: inline::llama-guard
    config: {}
  agents:
  - provider_id: meta-reference
    provider_type: inline::meta-reference
    config:
      persistence_store:
        type: sqlite
        namespace: null
        db_path: ${env.SQLITE_STORE_DIR:~/.llama/distributions/ollama}/agents_store.db
  telemetry:
  - provider_id: meta-reference
    provider_type: inline::meta-reference
    config: {}
metadata_store:
  namespace: null
  type: sqlite
  db_path: ${env.SQLITE_STORE_DIR:~/.llama/distributions/ollama}/registry.db
models:
- metadata: {}
  model_id: ${env.INFERENCE_MODEL}
  provider_id: ollama
  provider_model_id: null
shields: []
server:
  port: 8321
  auth:
    provider_type: "oauth2_token"
    config:
      jwks:
        uri: "https://my-token-issuing-svc.com/jwks"
```

Let's break this down into the different sections. The first section specifies the set of APIs that the stack server will serve:
```yaml
apis:
- agents
- inference
- memory
- safety
- telemetry
```

## Providers
Next up is the most critical part: the set of providers that the stack will use to serve the above APIs. Consider the `inference` API:
```yaml
providers:
  inference:
  # provider_id is a string you can choose freely
  - provider_id: ollama
    # provider_type is a string that specifies the type of provider.
    # in this case, the provider for inference is ollama and it is run remotely (outside of the distribution)
    provider_type: remote::ollama
    # config is a dictionary that contains the configuration for the provider.
    # in this case, the configuration is the url of the ollama server
    config:
      url: ${env.OLLAMA_URL:http://localhost:11434}
```
A few things to note:
- A _provider instance_ is identified with an (id, type, configuration) triplet.
- The id is a string you can choose freely.
- You can instantiate any number of provider instances of the same type.
- The configuration dictionary is provider-specific.
- Notice that configuration can reference environment variables (with default values), which are expanded at runtime. When you run a stack server (via docker or via `llama stack run`), you can specify `--env OLLAMA_URL=http://my-server:11434` to override the default value.

## Resources

Finally, let's look at the `models` section:

```yaml
models:
- metadata: {}
  model_id: ${env.INFERENCE_MODEL}
  provider_id: ollama
  provider_model_id: null
```
A Model is an instance of a "Resource" (see [Concepts](../concepts/index)) and is associated with a specific inference provider (in this case, the provider with identifier `ollama`). This is an instance of a "pre-registered" model. While we always encourage the clients to always register models before using them, some Stack servers may come up a list of "already known and available" models.

What's with the `provider_model_id` field? This is an identifier for the model inside the provider's model catalog. Contrast it with `model_id` which is the identifier for the same model for Llama Stack's purposes. For example, you may want to name "llama3.2:vision-11b" as "image_captioning_model" when you use it in your Stack interactions. When omitted, the server will set `provider_model_id` to be the same as `model_id`.

## Server Configuration

The `server` section configures the HTTP server that serves the Llama Stack APIs:

```yaml
server:
  port: 8321  # Port to listen on (default: 8321)
  tls_certfile: "/path/to/cert.pem"  # Optional: Path to TLS certificate for HTTPS
  tls_keyfile: "/path/to/key.pem"    # Optional: Path to TLS key for HTTPS
```

### Authentication Configuration

The `auth` section configures authentication for the server. When configured, all API requests must include a valid Bearer token in the Authorization header:

```
Authorization: Bearer <token>
```

The server supports multiple authentication providers:

#### OAuth 2.0/OpenID Connect Provider with Kubernetes

The server can be configured to use service account tokens for authorization, validating these against the Kubernetes API server, e.g.:
```yaml
server:
  auth:
    provider_type: "oauth2_token"
    config:
      jwks:
        uri: "https://kubernetes.default.svc:8443/openid/v1/jwks"
        token: "${env.TOKEN:}"
        key_recheck_period: 3600
      tls_cafile: "/path/to/ca.crt"
      issuer: "https://kubernetes.default.svc"
      audience: "https://kubernetes.default.svc"
```

To find your cluster's jwks uri (from which the public key(s) to verify the token signature are obtained), run:
```
kubectl get --raw /.well-known/openid-configuration| jq -r .jwks_uri
```

For the tls_cafile, you can use the CA certificate of the OIDC provider:
```bash
kubectl config view --minify -o jsonpath='{.clusters[0].cluster.certificate-authority}'
```

For the issuer, you can use the OIDC provider's URL:
```bash
kubectl get --raw /.well-known/openid-configuration| jq .issuer
```

The audience can be obtained from a token, e.g. run:
```bash
kubectl create token default --duration=1h | cut -d. -f2 | base64 -d | jq .aud
```

The jwks token is used to authorize access to the jwks endpoint. You can obtain a token by running:

```bash
kubectl create namespace llama-stack
kubectl create serviceaccount llama-stack-auth -n llama-stack
kubectl create token llama-stack-auth -n llama-stack > llama-stack-auth-token
export TOKEN=$(cat llama-stack-auth-token)
```

Alternatively, you can configure the jwks endpoint to allow anonymous access. To do this, make sure
the `kube-apiserver` runs with `--anonymous-auth=true` to allow unauthenticated requests
and that the correct RoleBinding is created to allow the service account to access the necessary
resources. If that is not the case, you can create a RoleBinding for the service account to access
the necessary resources:

```yaml
# allow-anonymous-openid.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: allow-anonymous-openid
rules:
- nonResourceURLs: ["/openid/v1/jwks"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: allow-anonymous-openid
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: allow-anonymous-openid
subjects:
- kind: User
  name: system:anonymous
  apiGroup: rbac.authorization.k8s.io
```

And then apply the configuration:
```bash
kubectl apply -f allow-anonymous-openid.yaml
```

The provider extracts user information from the JWT token:
- Username from the `sub` claim becomes a role
- Kubernetes groups become teams

You can easily validate a request by running:

```bash
curl -s -L -H "Authorization: Bearer $(cat llama-stack-auth-token)" http://127.0.0.1:8321/v1/providers
```

#### Custom Provider
Validates tokens against a custom authentication endpoint:
```yaml
server:
  auth:
    provider_type: "custom"
    config:
      endpoint: "https://auth.example.com/validate"  # URL of the auth endpoint
```

The custom endpoint receives a POST request with:
```json
{
  "api_key": "<token>",
  "request": {
    "path": "/api/v1/endpoint",
    "headers": {
      "content-type": "application/json",
      "user-agent": "curl/7.64.1"
    },
    "params": {
      "key": ["value"]
    }
  }
}
```

And must respond with:
```json
{
  "access_attributes": {
    "roles": ["admin", "user"],
    "teams": ["ml-team", "nlp-team"],
    "projects": ["llama-3", "project-x"],
    "namespaces": ["research"]
  },
  "message": "Authentication successful"
}
```

If no access attributes are returned, the token is used as a namespace.

### Quota Configuration

The `quota` section allows you to enable server-side request throttling for both
authenticated and anonymous clients. This is useful for preventing abuse, enforcing
fairness across tenants, and controlling infrastructure costs without requiring
client-side rate limiting or external proxies.

Quotas are disabled by default. When enabled, each client is tracked using either:

* Their authenticated `client_id` (derived from the Bearer token), or
* Their IP address (fallback for anonymous requests)

Quota state is stored in a SQLite-backed key-value store, and rate limits are applied
within a configurable time window (currently only `day` is supported).

#### Example

```yaml
server:
  quota:
    kvstore:
      type: sqlite
      db_path: ./quotas.db
    anonymous_max_requests: 100
    authenticated_max_requests: 1000
    period: day
```

#### Configuration Options

| Field                        | Description                                                                |
| ---------------------------- | -------------------------------------------------------------------------- |
| `kvstore`                    | Required. Backend storage config for tracking request counts.              |
| `kvstore.type`               | Must be `"sqlite"` for now. Other backends may be supported in the future. |
| `kvstore.db_path`            | File path to the SQLite database.                                          |
| `anonymous_max_requests`     | Max requests per period for unauthenticated clients.                       |
| `authenticated_max_requests` | Max requests per period for authenticated clients.                         |
| `period`                     | Time window for quota enforcement. Only `"day"` is supported.              |

> Note: if `authenticated_max_requests` is set but no authentication provider is
configured, the server will fall back to applying `anonymous_max_requests` to all
clients.

#### Example with Authentication Enabled

```yaml
server:
  port: 8321
  auth:
    provider_type: custom
    config:
      endpoint: https://auth.example.com/validate
  quota:
    kvstore:
      type: sqlite
      db_path: ./quotas.db
    anonymous_max_requests: 100
    authenticated_max_requests: 1000
    period: day
```

If a client exceeds their limit, the server responds with:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "error": {
    "message": "Quota exceeded"
  }
}
```

## Extending to handle Safety

Configuring Safety can be a little involved so it is instructive to go through an example.

The Safety API works with the associated Resource called a `Shield`. Providers can support various kinds of Shields. Good examples include the [Llama Guard](https://ai.meta.com/research/publications/llama-guard-llm-based-input-output-safeguard-for-human-ai-conversations/) system-safety models, or [Bedrock Guardrails](https://aws.amazon.com/bedrock/guardrails/).

To configure a Bedrock Shield, you would need to add:
- A Safety API provider instance with type `remote::bedrock`
- A Shield resource served by this provider.

```yaml
...
providers:
  safety:
  - provider_id: bedrock
    provider_type: remote::bedrock
    config:
      aws_access_key_id: ${env.AWS_ACCESS_KEY_ID}
      aws_secret_access_key: ${env.AWS_SECRET_ACCESS_KEY}
...
shields:
- provider_id: bedrock
  params:
    guardrailVersion: ${env.GUARDRAIL_VERSION}
  provider_shield_id: ${env.GUARDRAIL_ID}
...
```

The situation is more involved if the Shield needs _Inference_ of an associated model. This is the case with Llama Guard. In that case, you would need to add:
- A Safety API provider instance with type `inline::llama-guard`
- An Inference API provider instance for serving the model.
- A Model resource associated with this provider.
- A Shield resource served by the Safety provider.

The yaml configuration for this setup, assuming you were using vLLM as your inference server, would look like:
```yaml
...
providers:
  safety:
  - provider_id: llama-guard
    provider_type: inline::llama-guard
    config: {}
  inference:
  # this vLLM server serves the "normal" inference model (e.g., llama3.2:3b)
  - provider_id: vllm-0
    provider_type: remote::vllm
    config:
      url: ${env.VLLM_URL:http://localhost:8000}
  # this vLLM server serves the llama-guard model (e.g., llama-guard:3b)
  - provider_id: vllm-1
    provider_type: remote::vllm
    config:
      url: ${env.SAFETY_VLLM_URL:http://localhost:8001}
...
models:
- metadata: {}
  model_id: ${env.INFERENCE_MODEL}
  provider_id: vllm-0
  provider_model_id: null
- metadata: {}
  model_id: ${env.SAFETY_MODEL}
  provider_id: vllm-1
  provider_model_id: null
shields:
- provider_id: llama-guard
  shield_id: ${env.SAFETY_MODEL}   # Llama Guard shields are identified by the corresponding LlamaGuard model
  provider_shield_id: null
...
```
