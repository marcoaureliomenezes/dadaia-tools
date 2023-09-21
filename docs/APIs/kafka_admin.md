# Kafka Admin

Classe `KafkaAdminAPI` segue o padrão de projeto Adapter, criado a partir da sdk `kafka-python` do python. Essa classe tem por objetivo de servir a projetos pessoais como uma interface única para o serviço, a nível de administrador, para o Apache Kafka com SDK em Python. Essa abordagem trás os seguintes benefícios:

- Centralizar alterações no que diz respeito a interações com a SDK primária (kafka-python);
- Possibilidade de extender funcionalidades;
- Criação de interface própria;

