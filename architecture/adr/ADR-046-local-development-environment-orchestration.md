# ADR: Local Development Environment Orchestration

*   **Status:** Accepted
*   **Date:** 2025-05-18
*   **Deciders:** Architecture Review Board, Lead Developers
*   **Consulted:** [List of individuals consulted (optional)]
*   **Informed:** [List of individuals to be informed (optional)]

## Context and Problem Statement

Managing local development environments for a microservices-based e-commerce platform presents significant challenges. Developers need to run multiple services concurrently, manage their dependencies, ensure consistent configurations, and iterate quickly on code changes. The current ad-hoc approach (e.g., manual `docker-compose` scripts, individual service startups) leads to:
*   Increased onboarding time for new developers.
*   Inconsistent development environments across team members.
*   Difficulty in reproducing issues found in integrated environments.
*   Slow feedback loops for code changes.
*   Complexity in managing inter-service dependencies and configurations.

A standardized and automated local development orchestration tool is needed to streamline this process, improve developer productivity, and ensure a consistent and efficient development experience.

## Decision Drivers

*   **Developer Productivity:** Minimize time spent on environment setup and management.
*   **Speed of Iteration:** Enable fast feedback loops with live reloading and quick rebuilds.
*   **Consistency:** Ensure all developers work with similar, reliable local environments.
*   **Ease of Onboarding:** Simplify the process for new team members to get their development environment up and running.
*   **Scalability:** Support a growing number of microservices and developers.
*   **Resource Efficiency:** Optimize the use of local machine resources.
*   **Integration with Existing Tooling:** Compatibility with Docker, Kubernetes, and CI/CD pipelines.

## Considered Options

### Option 1: Status Quo (Manual Scripts & Docker Compose)

*   Description: Continue using individual shell scripts and `docker-compose.yaml` files managed per service or on an ad-hoc basis.
*   Pros:
    *   No new tools to learn.
    *   Flexibility for individual service needs.
*   Cons:
    *   Highly prone to inconsistencies.
    *   Difficult to manage inter-service dependencies comprehensively.
    *   Slow onboarding for new developers.
    *   No centralized view or control over the local environment.
    *   Live reloading and rapid iteration are often manual or poorly implemented.

### Option 2: Enhanced Docker Compose with Custom Scripting

*   Description: Develop a more sophisticated set of shared Docker Compose files and accompanying scripts to manage the entire local environment.
*   Pros:
    *   Leverages familiar Docker Compose syntax.
    *   More centralized than ad-hoc scripts.
*   Cons:
    *   Scripts can become complex and hard to maintain.
    *   Lacks a dedicated UI for managing services.
    *   Limited capabilities for smart rebuilds or live updates without significant custom effort.
    *   Still requires considerable manual effort to orchestrate complex scenarios.

### Option 3: Skaffold

*   Description: Use Skaffold, a command-line tool from Google, that facilitates continuous development for Kubernetes-native applications. It handles the workflow for building, pushing, and deploying applications.
*   Pros:
    *   Strong integration with Kubernetes.
    *   Automates build and deploy cycles.
    *   Supports various build tools and deployment strategies.
    *   File synchronization and hot reloading capabilities.
*   Cons:
    *   Primarily focused on Kubernetes; might be overkill if not all local development mimics K8s closely.
    *   Configuration can be complex (Skaffold.yaml).
    *   Steeper learning curve compared to simpler tools if not already familiar with K8s concepts.

### Option 4: Tilt.dev

*   Description: Use Tilt.dev, a tool for automating and managing local development environments, especially for microservices and Kubernetes. It uses a `Tiltfile` (written in Starlark, a Python dialect) to define how services are built, deployed, and updated.
*   Pros:
    *   Provides a web UI for observing and managing services.
    *   Optimized for fast feedback loops with live updates and smart rebuilds.
    *   Flexible `Tiltfile` API for defining complex workflows.
    *   Can manage both containerized (Kubernetes/Docker) and local (non-containerized) processes.
    *   Extensible via its API and extension system.
*   Cons:
    *   Introduces a new tool and configuration language (Starlark) to learn.
    *   Can consume significant local resources if not configured carefully.
    *   Relatively newer compared to some alternatives, though community and features are growing.

### Option 5: Telepresence

*   Description: Use Telepresence to connect a locally running service to a remote Kubernetes cluster. It proxies network traffic, environment variables, and volumes between the local machine and the remote cluster, making the local service behave as if it's running within the cluster.
*   Pros:
    *   Develop against actual dependencies in a shared remote Kubernetes cluster.
    *   Lightweight on local machine resources as only the target service runs locally.
    *   Full access to local development tools (IDEs, debuggers).
    *   Fast iteration for the locally developed service.
    *   Preview URLs allow sharing the local service with others.
*   Cons:
    *   Requires a stable connection to a remote Kubernetes cluster.
    *   Not a solution for fully offline local development.
    *   Potential for differences between local OS and container environment if not managed.
    *   Managing multiple local services that all need to interact within the same proxied environment can become complex.
    *   Can introduce network latency affecting the local service's interaction with remote services.

#### Tiltfile API for Orchestration

Tilt.dev utilizes a `Tiltfile`, written in Starlark (a Python dialect), to define the development environment. Key functions include:

*   **Image Building:**
    *   `docker_build(ref, context, dockerfile=None, build_args=None, live_update=[])`: Builds Docker images. The `live_update` feature allows for syncing local file changes directly into running containers without a full image rebuild and restart, significantly speeding up iteration.
    *   `custom_build(ref, command, deps, live_update=[])`: Allows using custom scripts or commands to build images, offering flexibility beyond standard Dockerfile builds. Also supports `live_update`.

*   **Kubernetes Resource Management:**
    *   `k8s_yaml(yaml)`: Loads Kubernetes manifest files (YAML) or `Blob`s of YAML content. Tilt intelligently discovers image dependencies and applies the manifests. It also watches YAML files for changes.
    *   `k8s_resource(workload, port_forwards=[], new_name=None, ...)`: Configures how Tilt manages specific Kubernetes workloads (Deployments, StatefulSets, etc.) defined by `k8s_yaml` or other K8s functions. This allows for setting up port forwards, defining dependencies between resources, grouping in the UI with labels, and customizing update behavior.
    *   `helm(chart_path, name=None, namespace=None, values=None, ...)`: Renders a Helm chart and makes its output available to `k8s_yaml` or `k8s_resource`.
    *   `kustomize(path_to_dir)`: Runs `kustomize build` on a directory and returns the resulting YAML as a `Blob` for use with `k8s_yaml`.
    *   `k8s_kind(kind_name, image_json_path=None, ...)`: Informs Tilt about Custom Resource Definitions (CRDs), enabling it to find image references and manage pods for custom Kubernetes objects.
    *   `k8s_custom_deploy(name, apply_cmd, delete_cmd, deps=[])`: For integrating with deployment tools that have their own CLI commands for applying and deleting resources, rather than using `kubectl apply -f`.

*   **Local Process Management:**
    *   `local_resource(name, cmd=None, serve_cmd=None, deps=[])`: Manages non-containerized processes running directly on the host machine. `cmd` is for one-off tasks (e.g., a build step), while `serve_cmd` is for long-running processes (e.g., a dev server). `deps` specifies files/directories to watch for changes to trigger updates. This is useful for frontends, linters, or any part of the stack not running in Docker/Kubernetes.

*   **Configuration & Utilities:**
    *   `allow_k8s_contexts(contexts)`: Restricts Tilt to operate only on specified Kubernetes contexts, preventing accidental deployments to production.
    *   `load(module_path, *symbols)`: Imports functions or variables from other Tiltfiles or extensions, promoting modularity.
    *   `fail(msg)` / `exit(msg)`: Allows programmatic termination of the Tiltfile execution with an error message.
    *   `read_json(path)` / `read_file(path)`: Reads files from the local system.

These functions provide a comprehensive toolkit to define how services are built, (re)deployed, and interconnected in a local development environment, enabling fast iteration cycles and a clear overview of the system state.

## Decision Outcome

**Chosen Option:** Tilt.dev for overall environment orchestration, combined with Telepresence for focused, in-cluster local development and debugging of individual services.

**Reasoning:**
The combination of Tilt.dev and Telepresence is chosen because it directly addresses the core challenges of local microservice development outlined in the problem statement and aligns strongly with our decision drivers:

*   **Addresses Problem Statement:** This combination tackles inconsistent environments, slow feedback loops, and onboarding complexity. Tilt provides a standardized way to define and manage the entire local (or dev-cluster-connected) environment, ensuring all services are built and run consistently. Telepresence then allows developers to seamlessly inject their locally running service into this Tilt-managed cluster environment, interacting with real dependencies.

*   **Developer Productivity & Speed of Iteration:** Tilt's `live_update` and automatic rebuilds for the overall environment, coupled with Telepresence's ability to hot-reload/debug a single service locally while it communicates with the cluster, drastically reduces wait times and accelerates iteration cycles. Developers get immediate feedback on their specific service without waiting for full environment rebuilds.

*   **Consistency & Ease of Onboarding:** Tilt ensures the base environment (whether fully local K8s or a shared dev K8s cluster) is consistent for everyone. For a new developer, `tilt up` brings up the world. To work on a specific service, they use a standard Telepresence command to intercept it. This is significantly simpler than manually configuring numerous services and their interactions.

*   **Resource Efficiency & Scalability:** With Telepresence, only the actively developed service runs on the local machine, while other services run in the Kubernetes cluster (local or remote). This greatly reduces local resource consumption, making it feasible to work with a large number of microservices without overwhelming developer laptops. Tilt efficiently manages these cluster resources.

*   **Integration with Existing Tooling (Kubernetes Focus):** Given our commitment to Kubernetes (ADR-006), both Tilt and Telepresence are designed for Kubernetes-native development. Tilt orchestrates deployments to K8s, and Telepresence bridges the local development machine with a K8s cluster.

*   **Preference over other options:**
    *   **Status Quo/Enhanced Docker Compose:** These lack the sophisticated orchestration, UI, Kubernetes-native focus, and the seamless in-cluster debugging capabilities offered by the Tilt+Telepresence combination. They would require significant custom scripting to achieve a fraction of the benefits.
    *   **Skaffold (standalone):** While powerful for K8s, Skaffold alone doesn't offer the same elegant solution as Telepresence for proxying a local service into a cluster. Combining Skaffold with Telepresence is a viable alternative, but Tilt's UI and specific focus on the local development experience (including `local_resource`) give it an edge for a comprehensive local orchestration solution.
    *   **Tilt (standalone):** Powerful for managing services in a local K8s cluster, but adding Telepresence elevates the experience by allowing developers to work on a service locally with their preferred tools while it behaves as if it's inside the cluster, reducing the need to constantly push image changes even for small iterations when focused on a single service.
    *   **Telepresence (standalone):** Excellent for bridging a local service to a remote cluster, but it doesn't manage the cluster environment itself. Tilt provides this crucial orchestration layer.

This hybrid approach leverages Tilt's strength in defining and managing the multi-service environment and Telepresence's strength in providing a fast, high-fidelity inner-loop experience for individual service development.

### Positive Consequences
*   **Improved Developer Productivity & Faster Iteration:** Tilt's live updates and Telepresence's local service interception will significantly speed up the code-build-test-debug cycle.
*   **Enhanced Environment Consistency:** All developers will use Tilt to define and manage the base environment, reducing "works on my machine" issues.
*   **Simplified Onboarding:** New developers can get a complex microservices environment running with `tilt up` and then use standard Telepresence commands to work on specific services, reducing initial setup friction.
*   **Reduced Local Resource Consumption:** By running most services in a Kubernetes cluster (local or remote) and only the actively developed service locally via Telepresence, developer machines will be less burdened.
*   **Higher Fidelity Development & Testing:** Developing services that interact directly with other real services and dependencies within a Kubernetes cluster (facilitated by Telepresence) leads to more realistic testing and earlier detection of integration issues.
*   **Better Debugging Capabilities:** Developers can use their preferred local IDEs and debuggers directly on code that is effectively running as part of the larger, cluster-hosted application.
*   **Stronger Alignment with Production:** Development practices will more closely mirror the Kubernetes-based production environment (ADR-006).

### Negative Consequences (and Mitigations)
*   **Increased Tooling Complexity & Learning Curve:**
    *   *Drawback:* Developers need to learn Tilt (including its Starlark-based Tiltfile) and Telepresence commands and concepts, in addition to existing tools like Docker and Kubernetes basics.
    *   *Mitigation:* Provide comprehensive internal documentation, hands-on training workshops, and standardized `Tiltfile` templates. Designate subject matter experts or champions for Tilt and Telepresence. Start with core functionality and introduce advanced features progressively.

*   **Dependency on a Kubernetes Cluster:**
    *   *Drawback:* The workflow relies on a functioning Kubernetes cluster (either local like Minikube/Kind or a shared remote development cluster). Setup and maintenance of these clusters can introduce overhead.
    *   *Mitigation:* For local clusters, provide clear, opinionated setup scripts and minimum resource recommendations. For shared remote clusters, ensure they are stable, well-resourced, and developers have appropriate namespaces and RBAC. Invest in automating cluster provisioning and maintenance where possible.

*   **Network Reliability for Remote Telepresence:**
    *   *Drawback:* If Telepresence is primarily used with a remote Kubernetes cluster, developer experience can be impacted by network latency or instability.
    *   *Mitigation:* Ensure developers have access to stable and performant network connections. Offer guidance on using a local Kubernetes cluster (managed by Tilt) as an alternative for periods of poor connectivity to remote resources. For services less dependent on remote-only resources, encourage local cluster usage.

*   **Debugging the Development Tools Themselves:**
    *   *Drawback:* When issues arise, it might be challenging to determine if the root cause is in the application code, Tilt configuration, Telepresence proxying, or the Kubernetes cluster itself.
    *   *Mitigation:* Foster a culture of knowledge sharing. Encourage active participation in the official Tilt and Telepresence community channels (e.g., Slack) for support. Document common troubleshooting steps and solutions internally. Ensure developers are familiar with accessing and interpreting logs from Tilt and Telepresence.

*   **Initial Setup and Configuration Effort:**
    *   *Drawback:* Crafting comprehensive `Tiltfile`s for a large number of microservices and establishing optimal Telepresence intercept strategies will require a significant upfront investment of time and effort.
    *   *Mitigation:* Prioritize a phased rollout, starting with a few key services or a single team to refine the patterns. Develop reusable Tiltfile functions and modules. Establish clear conventions for service configuration to simplify integration.

### Neutral Consequences
*   **Shift in Local Development Paradigm:** The development workflow will become more Kubernetes-centric, even if a local Kubernetes cluster (like Minikube or Kind) is used. This represents a shift from potentially more isolated `docker-compose` setups for some developers towards interacting with a K8s API and concepts more regularly during local development.
*   **Increased Reliance on Shared Tooling Configuration:** While individual service code remains independent, the way services are built, deployed locally, and managed will be more tightly coupled to the shared `Tiltfile` configurations and Telepresence usage patterns adopted by the team.
*   **Potential for More Abstracted Local Environment:** Developers might have less direct interaction with the underlying Docker daemons or individual container runtime details for services managed by Tilt/Telepresence, as these tools provide an abstraction layer.

## Links (Optional)

*   [Tilt.dev Official Documentation](https://docs.tilt.dev/)
*   [Skaffold Official Documentation](https://skaffold.dev/docs/)
*   [Docker Compose Documentation](https://docs.docker.com/compose/)
*   [ADR-001-adoption-of-microservices-architecture.md](./ADR-001-adoption-of-microservices-architecture.md)
*   [ADR-006-cloud-native-deployment-strategy.md](./ADR-006-cloud-native-deployment-strategy.md)

## Future Considerations (Optional)

*   [Any follow-up actions, potential future work, or aspects to monitor related to this decision.]

## Rejection Criteria (Optional)

*   Under what circumstances would this decision be revisited or overturned?
