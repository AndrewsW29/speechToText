---
source_url: https://junit.org/junit5/docs/current/user-guide/
language: java
framework: junit
artifact_type: test
---
To write a unit test for a service with JUnit 5, create a test class and annotate each test method with Test. Replace the repository with a mock created by Mockito and inject it into the service through the constructor. Arrange the mock behavior with when and thenReturn, call the service method and assert the result with assertEquals. Use ExtendWith with MockitoExtension to initialize the mocks. Name tests after the behavior they check.
