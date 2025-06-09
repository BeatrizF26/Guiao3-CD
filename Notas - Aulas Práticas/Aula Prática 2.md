## Ordem de trabalhos

### Consumidores
- Criar a Queue e no construtor também colocar o tópico em que está interessado, envia logo uma mensagem de subscrição ao broker.
- Fazer o método push
- Pode fazer um pull e não ficar à espera de nada, impedindo que o broker guarde o valor da publicação (Só pode 'guardar' até 1)
  - ***Nota:*** Primeiro pull não espera porque recebe o valor da última publicação, mas o segundo pull já vai estar à espera que o valor da publicação seja alterado

- ***Nota:*** Push -> Mandar a mensagem pelo broker
- ***Nota:*** Pull -> Ler a mensagem do broker e descodificar

### Produtores
- Criar a Queue
- Ligar à socket (Vão ser usadas sockets TCP)
  - ***Nota:*** O broker vai ter uma socket para cada um dos produtores, ou seja, vai ser preciso seletores
  

## Mensagens Possíveis
- Publicação
- Subscrição
- Cancelamento da subscrição
- Listagem de Tópicos
  - Broker não sabe se a próxima mensagem que vai receber é a resposta a essa mensagem
  - Pode processar primeiro a publicação de um tópico A do que a listagem de tópicos
- #### ***Resolução:*** 
    Na queue, a listagem de tópicos não fica à espera de receber a lista, ele regista internamente no callback, que é a função para onde ele vai receber as informações (através do método pull)

## Problema da primeira mensagem

- Trabalhar com um header de 1 byte que indica se a mensagem é JSON/Picket/XML

## Como testar
### Terminal 1
    $python3 producer.py --topic /temp --queue_type json

### Terminal 2
    $python3 consumer.py --topic /temp --queue_type pickle

- ***Nota:*** Se não se colocar a flag queue_type, ele vai assumir que o tipo vai ser JSON, por isso tem de se mudar para o que pretendemos


## protocol.py
- **SubscribeTopicMessage:** {"command" : sub, "topic" : topic}
- **PublishTopic:** {"command" : pub, "topic" : topic, "message" : msg}
- **RequestTopic:** {"command" : request}
- **CancelTopicMessage:** {"command" : cancel, "topic" : topic} 

***Nota:*** No pull fazer a verificação da mensagem que se está a receber
