# Padrão de testes utilizado na API

## Requisito

> Utilizar um padrão de testes e indicar onde será utilizado e como.

## Resposta

A API PostgreSQL do sistema Delta utilizará a metodologia **TDD (Test-Driven Development)** durante o desenvolvimento de novas funcionalidades e correções de regras de negócio. Os testes serão estruturados com o padrão **AAA (Arrange, Act e Assert)**.

O TDD orienta o momento em que os testes e o código de produção são escritos. O AAA define como o conteúdo de cada teste será organizado. A utilização dos dois conceitos permite atender ao requisito com uma estratégia clara e aplicável a todos os módulos atuais e futuros da API.

## Tecnologias utilizadas

O projeto já possui a dependência `spring-boot-starter-test` no arquivo `pom.xml`:

Essa dependência disponibiliza ferramentas utilizadas nos testes, como:

- **JUnit 5:** criação e execução dos testes;
- **Mockito:** criação de mocks para simular dependências;
- **AssertJ:** escrita de verificações legíveis;
- **Spring Boot Test:** suporte para testes web e de integração.

## Metodologia TDD

No TDD, o teste é escrito antes da implementação da funcionalidade. O desenvolvimento segue o ciclo **Red, Green e Refactor**:

```text
RED → GREEN → REFACTOR
```

### Red — escrever um teste que falha

Primeiro, é criado um teste que descreve o comportamento esperado para uma funcionalidade ainda não implementada. Ao executar o teste, ele deve falhar pelo motivo esperado.

Exemplos de comportamentos que podem iniciar um ciclo de TDD:

- cadastrar um recurso quando os dados forem válidos;
- impedir o cadastro de um recurso duplicado;
- retornar erro quando um registro não for encontrado;
- rejeitar uma mudança de estado não permitida;
- validar um relacionamento entre entidades;
- aplicar corretamente um cálculo ou regra de negócio.

### Green — implementar o necessário

Em seguida, é escrito o código mínimo necessário para que o teste seja aprovado. Nessa etapa, o objetivo é atender ao comportamento definido pelo teste.

### Refactor — melhorar o código

Depois que o teste passa, o código pode ser reorganizado para melhorar nomes, remover duplicações e separar responsabilidades. Os testes são executados novamente para confirmar que o comportamento não foi alterado.

## Padrão AAA

Os testes serão organizados com o padrão **AAA**, que divide cada cenário em três partes:

1. **Arrange (Preparação):** criação dos dados e configuração das dependências simuladas;
2. **Act (Ação):** execução do método ou comportamento testado;
3. **Assert (Verificação):** confirmação do resultado esperado.

Exemplo genérico de teste unitário:

```java
@Test
void deveLancarExcecaoQuandoRecursoJaExistir() {
    // Arrange
    var entrada = criarEntradaValida();

    when(repository.existsByIdentifier(anyString()))
            .thenReturn(true);

    // Act
    Executable action = () -> service.create(entrada);

    // Assert
    assertThrows(
            ResourceAlreadyExistsException.class,
            action
    );

    verify(repository, never()).save(any());
}
```

O exemplo representa uma estrutura que poderá ser adaptada às classes e regras de qualquer módulo da API.

## Onde os testes serão utilizados

Os testes ficarão em `src/test/java` e seguirão a mesma estrutura de pacotes existente em `src/main/java`.

Estrutura esperada:

```text
src/main/java/.../modules/
└── nome_do_modulo/
    ├── controller/
    ├── service/
    ├── repository/
    ├── mapper/
    ├── dto/
    └── entity/

src/test/java/.../modules/
└── nome_do_modulo/
    ├── controller/
    ├── service/
    ├── repository/
    └── mapper/
```

Cada classe de teste utilizará o nome da classe testada seguido de `Test`:

```text
NomeDoModuloService     → NomeDoModuloServiceTest
NomeDoModuloController  → NomeDoModuloControllerTest
NomeDoModuloRepository  → NomeDoModuloRepositoryTest
NomeDoModuloMapper      → NomeDoModuloMapperTest
```

Essa convenção será utilizada em todos os módulos atuais e futuros, sem vincular a estratégia a uma entidade específica.

## Aplicação por camada

### Camada Service

As classes `Service` serão verificadas principalmente com **testes unitários**. Os repositórios e mappers serão simulados com Mockito para que somente a regra de negócio da classe seja testada.

Serão verificados cenários como:

- operações realizadas com sucesso;
- tentativa de cadastrar dados duplicados;
- busca de registros inexistentes;
- validação de relacionamentos;
- mudanças de estado permitidas e proibidas;
- interação correta com os repositórios.

Estrutura genérica:

```java
@ExtendWith(MockitoExtension.class)
class NomeDoModuloServiceTest {

    @Mock
    private NomeDoModuloRepository repository;

    @Mock
    private NomeDoModuloMapper mapper;

    @InjectMocks
    private NomeDoModuloService service;
}
```

### Camada Controller

Os controllers serão verificados com **testes da camada web**, utilizando `@WebMvcTest` e `MockMvc`.

Esses testes deverão confirmar:

- o endereço dos endpoints;
- os métodos HTTP utilizados;
- os códigos de resposta, como `200`, `201`, `204`, `400`, `404` e `409`;
- a validação dos dados de entrada;
- o formato JSON enviado e recebido;
- a integração com o tratamento global de exceções.

### Camada Repository

Consultas personalizadas e mapeamentos JPA relevantes serão verificados com **testes de persistência**, utilizando `@DataJpaTest`.

Esses testes deverão confirmar:

- o funcionamento de consultas derivadas ou personalizadas;
- a persistência e recuperação de entidades;
- relacionamentos entre entidades;
- restrições de integridade e unicidade.

Não será necessário testar individualmente todos os métodos prontos de `JpaRepository`, pois eles já pertencem ao Spring Data JPA. O foco estará nas consultas e comportamentos específicos da aplicação.

### Camada Mapper

Os mappers serão verificados com testes unitários simples para confirmar:

- a conversão de requisições em objetos internos;
- a conversão de DTOs em entidades;
- a conversão de entidades em objetos de resposta;
- a preservação dos valores durante as conversões.

### Testes de integração

Testes de integração serão utilizados nos fluxos mais importantes para verificar o funcionamento conjunto de diferentes camadas da aplicação.

Eles poderão utilizar `@SpringBootTest` para validar situações em que seja necessário carregar o contexto completo do Spring. Como esses testes são mais lentos, serão usados em menor quantidade do que os testes unitários.


## Conclusão

A API atenderá ao requisito utilizando **TDD** como metodologia de desenvolvimento e **AAA** como padrão de organização dos testes. O TDD será aplicado durante a criação de novas funcionalidades e regras de negócio por meio do ciclo Red, Green e Refactor. O padrão AAA será utilizado para separar a preparação, a execução e a verificação de cada cenário.

A estratégia será aplicada a todos os módulos da API. As regras de negócio serão verificadas com testes unitários, os endpoints com testes web, as consultas específicas com testes de persistência, os mappers com testes de conversão e os principais fluxos com testes de integração.
