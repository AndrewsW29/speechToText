---
source_url: https://example.com/samples/UserService.java
language: java
framework: spring
artifact_type: service
content_type: code
---
package demo;

@Service
public class UserService {
  private final UserRepository repository;

  public UserService(UserRepository repository) {
    this.repository = repository;
  }

  public List<User> findAll() {
    return repository.findAll();
  }
}
