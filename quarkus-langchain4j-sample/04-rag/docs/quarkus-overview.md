# Quarkus Overview

Quarkus is a Java framework tailored for deployment on Kubernetes. Key technology components surrounding it are OpenJDK HotSpot and GraalVM. Quarkus aims to make Java a leading platform in Kubernetes and serverless environments while offering developers a unified reactive and imperative programming model to address a wider range of distributed application architectures optimally.

Quarkus offers quick scale-up and high-density use in container orchestration platforms such as Kubernetes. Many more application instances can be run given the same hardware resources. After its initial debut, Quarkus underwent several enhancements over the next few months, culminating in a 1.0.0 release within the open-source community in November 2019.

## Design pillars

### Container first

From the beginning, Quarkus was designed around the container-first and Kubernetes-native philosophy, optimizing for low memory usage and fast startup times.

As much processing as possible is done at build time, including taking a closed-world assumption approach to building and running applications. This optimization means that, in most cases, all code that does not have an execution path at runtime isn't loaded into the JVM.

In Quarkus, classes used only at application startup are invoked at build time and not loaded into the runtime JVM. Quarkus also avoids reflection as much as possible, instead favoring static class binding. These design principles reduce the size, and ultimately the memory footprint, of the application running on the JVM while also enabling Quarkus to be natively-native.

Quarkus' design accounted for native compilation from the outset. It was optimized for using the native image capability of GraalVM to compile JVM bytecode to a native machine binary. GraalVM aggressively removes any unreachable code found within the application's source code as well as any of its dependencies. Combined with Linux containers and Kubernetes, a Quarkus application runs as a native Linux executable, eliminating the JVM. A Quarkus native executable starts much faster and uses far less memory than a traditional JVM.

* Fast Startup (tens of milliseconds) allows automatic scaling up and down of microservices on containers and Kubernetes, as well as FaaS on-the-spot execution
* Low memory use helps optimize container density in microservices architecture deployments requiring multiple containers
* Smaller application and container image footprint

### Unify reactive and imperative

Quarkus combines both reactive and imperative programming models in a single, unified programming model that lets developers use the right approach for the right job, without having to learn multiple frameworks. Quarkus is based on a solid reactive core powered by Eclipse Vert.x and Netty, enabling the use of the reactive programming model when writing applications.

### Developer joy

Quarkus provides a cohesive platform for developers, backed by a strong extension framework, to make building applications simpler and more enjoyable, through features such as:

* Unified configuration
* Live coding (change your code, see the change applied immediately, no restart needed)
* Streamlined code for the most common tasks, with sane defaults
* No hassle native executable generation
* Quarkus Dev Services, which spin up external services (databases, message brokers, and more) automatically in dev and test mode

## Standards-based

Quarkus is built on top of standards, such as JAX-RS, CDI (Contexts and Dependency Injection), and MicroProfile, allowing developers to leverage their existing knowledge of the Java ecosystem.
