# ADR: Primary Programming Language and Framework for Initial Services (Node.js with NestJS)

*   **Status:** Accepted
*   **Date:** 2025-05-11 (User to confirm/update actual decision date)
*   **Deciders:** Project Team
*   **Consulted:** (N/A - can be updated if specific team expertise was leveraged)
*   **Informed:** All technical stakeholders

## Context and Problem Statement

For the initial development phase of the e-commerce platform, particularly for services like User Management, a decision is needed on the primary programming language and web framework. This choice will impact developer productivity, performance, type safety, ecosystem support, hiring, and the speed of initial service delivery. The goal is to select a stack that aligns with modern practices, supports asynchronous operations for I/O-bound services, offers strong typing, and provides a good balance of performance and structured development.

## Decision Drivers

*   **Developer Productivity & Maintainability:** Ability to build robust, maintainable services efficiently, supported by strong typing and a structured framework.
*   **Performance for I/O-Bound Services:** Excellent performance for typical e-commerce service loads, leveraging non-blocking I/O.
*   **Ecosystem & Libraries (NPM):** Access to a vast collection of libraries for common tasks.
*   **Asynchronous Support:** Innate non-blocking, event-driven architecture.
*   **Type Safety:** Leveraging TypeScript for compile-time error checking and improved code quality.
*   **Full-Stack Potential:** Ability to use JavaScript/TypeScript across both frontend and backend.
*   **Community & Enterprise Adoption:** A growing and active community, with increasing adoption in enterprise settings.
*   **Scalability and Microservice Suitability:** Well-suited for building scalable microservices.

## Considered Options

### Option 1: Node.js with NestJS (using TypeScript)

*   **Description:** Using Node.js as the runtime, TypeScript as the programming language, and NestJS as the web framework. NestJS is a progressive Node.js framework for building efficient, reliable, and scalable server-side applications, built with and fully supporting TypeScript.
*   **Pros:**
    *   **Strong Typing with TypeScript:** Enhances code quality, maintainability, and reduces runtime errors. Excellent for larger teams and complex applications.
    *   **Structured & Modular Architecture:** NestJS provides an opinionated, Angular-inspired architecture (modules, controllers, services, dependency injection) which promotes organization and scalability.
    *   **Excellent Performance for I/O-Bound Tasks:** Leverages Node.js's non-blocking, event-driven nature.
    *   **Large NPM Ecosystem:** Access to a vast number of libraries and tools.
    *   **Full-Stack JavaScript/TypeScript:** Potential for code sharing and unified skill sets if the frontend also uses TypeScript/JavaScript.
    *   **Good Support for Microservice Patterns:** Built-in support for various transport layers (TCP, Redis, gRPC, Kafka, NATS) and microservice concepts.
    *   **Automatic API Documentation:** Integrates well with tools like Swagger (OpenAPI).
    *   **Active Community and Growing Popularity.**
*   **Cons:**
    *   **Learning Curve for Opinionated Framework:** NestJS has a steeper learning curve than more minimalist Node.js frameworks like Express if developers are unfamiliar with its specific structure (similar to Angular).
    *   **Single-Threaded Nature of Node.js:** CPU-bound tasks can block the event loop. Requires worker threads or offloading for intensive computations.
    *   **Build Step for TypeScript:** Requires compilation from TypeScript to JavaScript.

### Option 2: Python with FastAPI

*   **Description:** Using Python and the FastAPI framework.
*   **Pros:**
    *   High developer productivity and concise syntax.
    *   Good performance, especially with native async support.
    *   Automatic API documentation and data validation with Pydantic.
    *   Rich Python ecosystem.
*   **Cons:**
    *   GIL can limit CPU-bound performance in a single process.
    *   Type hinting is excellent but TypeScript offers a more comprehensive and compile-time enforced type system.
    *   Less opinionated structure compared to NestJS, potentially leading to more variability in larger projects if not carefully managed.

### Option 3: Java with Spring Boot

*   **Description:** Using Java and the Spring Boot framework.
*   **Pros:**
    *   Mature, robust ecosystem, very strong for enterprise applications.
    *   Excellent performance and scalability.
    *   Strongly typed language.
*   **Cons:**
    *   Higher verbosity and potentially slower development.
    *   Higher resource consumption.
    *   Longer startup times.

### Option 4: Go (Golang) with Gin/Echo

*   **Description:** Using Go with a lightweight web framework.
*   **Pros:**
    *   Exceptional performance and concurrency.
    *   Low resource footprint, statically typed.
*   **Cons:**
    *   Smaller web application ecosystem compared to Node.js/Python/Java.
    *   Error handling verbosity.
    *   Potentially steeper learning curve for its concurrency model.

## Decision Outcome

**Chosen Option:** Node.js with NestJS (using TypeScript)

**Reasoning:**
Node.js with NestJS is chosen as the primary technology stack for the initial set of services. This decision is driven by the desire for a highly productive, scalable, and maintainable platform, with a strong emphasis on type safety and modern development practices provided by TypeScript and the structured nature of NestJS.

NestJS's architecture promotes building well-organized, testable, and scalable microservices. The non-blocking I/O of Node.js is well-suited for I/O-bound e-commerce services. The ability to use TypeScript across the stack (if applicable to the frontend) is also a significant advantage for team synergy and code consistency. The extensive NPM ecosystem provides ready-to-use solutions for many common problems.

While CPU-bound tasks require careful handling in Node.js, most e-commerce microservices are predominantly I/O-bound, where Node.js excels. The benefits of TypeScript's strong typing, combined with NestJS's robust framework features (dependency injection, modules, microservice support), make it a compelling choice for building the initial services of the platform.

### Positive Consequences
*   Enhanced code quality, refactorability, and maintainability due to TypeScript and NestJS's structured approach.
*   Excellent performance for I/O-bound microservices.
*   Improved developer experience with features like dependency injection and a modular design.
*   Access to the vast NPM library ecosystem.
*   Potential for full-stack development using TypeScript.
*   Good built-in support for microservice patterns and transports.

### Negative Consequences (and Mitigations)
*   **Node.js Single-Threaded Limitation for CPU-Bound Tasks:**
    *   **Mitigation:** For any truly CPU-bound tasks, offload to worker threads, separate processes, or consider services written in other more suitable languages. Microservices will be scaled horizontally.
*   **Learning Curve for NestJS:** The opinionated nature of NestJS might require an initial learning investment for developers new to it.
    *   **Mitigation:** Provide adequate training resources, documentation, and internal workshops. Leverage the comprehensive official NestJS documentation.
*   **Build Step Overhead:** TypeScript requires a compilation step to JavaScript.
    *   **Mitigation:** Modern build tools and CI/CD pipelines can make this process efficient and largely transparent to developers.

### Neutral Consequences
*   Sets a strong precedent for the initial services. While polyglot persistence and services are principles, a consistent primary stack aids in initial velocity and shared learning.

## Links

*   (Potentially: Link to `02-user-management-service.md` once updated to reflect NestJS)
*   [E-commerce Platform: System Architecture Overview](../00-system-architecture-overview.md)

## Future Considerations

*   Establish clear project conventions, code style guides, and best practices for NestJS development.
*   Develop a common library or set of shared modules for NestJS services to handle cross-cutting concerns like logging, configuration, error handling, etc.
*   Continuously evaluate performance and consider other technologies if specific services have unique NFRs not optimally met by NestJS.

## Rejection Criteria

*   If critical performance issues directly attributable to Node.js/NestJS for core I/O-bound services are discovered and cannot be mitigated.
*   If the learning curve or complexity of NestJS significantly impedes development velocity for an extended period.
