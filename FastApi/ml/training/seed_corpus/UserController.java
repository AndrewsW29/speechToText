---
source_url: https://example.com/samples/UserController.java
language: java
framework: spring
artifact_type: controller
content_type: code
---
package demo;

@RestController
@RequestMapping("/users")
public class UserController {
  private final UserService service;

  public UserController(UserService service) {
    this.service = service;
  }

  @GetMapping
  public List<User> list() {
    return service.findAll();
  }
}
