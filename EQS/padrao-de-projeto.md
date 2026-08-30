# Padrão de projeto utilizado na API

## Requisito

> Usar algum padrão de projeto e indicar em que parte do código ele foi utilizado.

## Resposta

A API utiliza o **Repository Pattern (Padrão Repository)** para separar o acesso ao banco de dados das regras de negócio da aplicação.

Esse padrão cria uma camada responsável pelas operações de persistência, como salvar, buscar, atualizar e excluir registros. Dessa forma, as classes de serviço não precisam executar comandos SQL nem conhecer os detalhes da comunicação com o PostgreSQL.

No projeto, o padrão foi implementado principalmente pelas interfaces dos módulos da API Device, Adress, Property... que estendem `JpaRepository`, do Spring Data JPA.

## Onde o padrão foi utilizado

### Repository do módulo Device

Arquivo: `src/main/java/br/com/delta/delta_api_postgres/modules/device/repository/DeviceRepository.java`

```java
public interface DeviceRepository extends JpaRepository<Device, Integer> {
    Optional<Device> findByDeviceId(String deviceId);

    boolean existsByDeviceId(String deviceId);
}
```

A interface representa o repositório da entidade `Device`. Por meio da extensão de `JpaRepository<Device, Integer>`, o Spring Data JPA disponibiliza operações como:

- `save`: salva ou atualiza um dispositivo;
- `findById`: procura um dispositivo pelo identificador;
- `findAll`: lista todos os dispositivos;
- `delete`: exclui um dispositivo.

Além dessas operações, foram declarados os métodos `findByDeviceId` e `existsByDeviceId`. O Spring cria suas implementações automaticamente a partir dos nomes dos métodos.

## Estrutura da aplicação

O Repository faz parte da organização em camadas adotada na API:

```text
Requisição HTTP
      ↓
DeviceController
      ↓
DeviceService
      ↓
DeviceRepository / PropertyRepository
      ↓
PostgreSQL
```

Cada componente possui uma responsabilidade:

- **Controller:** recebe as requisições HTTP e devolve as respostas;
- **Service:** executa as regras de negócio;
- **Repository:** abstrai o acesso ao banco de dados;
- **Entity:** representa os dados persistidos;
- **Mapper:** converte entidades, DTOs e objetos de entrada e saída.

## Benefícios obtidos

A aplicação do Repository Pattern proporciona:

- separação entre regras de negócio e persistência;
- redução do acoplamento com os detalhes do banco de dados;
- maior organização do código;
- facilidade para realizar testes;
- centralização das operações relacionadas a cada entidade;
- manutenção e evolução mais simples da aplicação.

## Relação com os princípios SOLID

O Repository Pattern também contribui para a aplicação de princípios SOLID:

- **Princípio da Responsabilidade Única (SRP):** os repositórios cuidam do acesso aos dados, enquanto os serviços cuidam das regras de negócio;
- **Princípio da Inversão de Dependência (DIP):** o serviço recebe interfaces de repositório por injeção de dependência, sem criar diretamente suas implementações.

## Conclusão

A API atende ao requisito por utilizar o **Repository Pattern** nas interfaces dos módulos. Essas interfaces abstraem o acesso ao PostgreSQL e são utilizadas pelas classes de serviço, como `DeviceService` e `PropertyService`, mantendo as operações de persistência separadas das regras de negócio.
