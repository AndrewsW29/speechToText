---
source_url: https://docs.spring.io/spring-data/jpa/reference/repositories/query-methods-details.html
language: java
framework: spring
artifact_type: repository
---
Spring Data JPA removes boilerplate from the persistence layer. Declare an interface that extends JpaRepository with the entity type and the id type, and Spring creates the implementation at runtime. Query methods are derived from their names, for example findByEmail or findByLastNameAndActiveTrue. For custom queries use the Query annotation with JPQL. Combine a repository with a service so that the controller never talks to the database directly.
