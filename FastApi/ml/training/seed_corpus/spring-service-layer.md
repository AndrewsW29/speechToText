---
source_url: https://docs.spring.io/spring-framework/reference/core/beans/classpath-scanning.html
language: java
framework: spring
artifact_type: service
---
A service class holds the business logic of the application. Annotate it with Service so Spring detects it during component scanning and registers it as a bean. Services sit between controllers and repositories: the controller calls the service and the service calls the repository. Keep transactions at the service layer with the Transactional annotation. To create a service, write a public class, add the Service annotation and receive its repository through the constructor.
