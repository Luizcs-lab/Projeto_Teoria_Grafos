🚀 Roteador para Transplantes Hospitalares em Mogi das Cruzes
Resumo: Este projeto desenvolve um roteador inteligente para otimizar o transporte de órgãos em Mogi das Cruzes. Utilizando o grafo de ruas da cidade, o sistema calcula as rotas mais eficientes (com base no menor tempo de viagem), incluindo a capacidade de encontrar o hospital mais próximo e considerar dados de tráfego em tempo real, visando agilizar operações críticas de transplante.

🎯 Objetivo
O objetivo principal deste projeto é fornecer uma ferramenta eficiente e intuitiva para o cálculo de rotas hospitalares na cidade de Mogi das Cruzes, com foco na otimização do tempo de viagem para o transporte de órgãos em situações de transplante. O sistema visa resolver o desafio de encontrar caminhos mais rápidos e confiáveis em um ambiente urbano complexo, minimizando o tempo de deslocamento que é crucial nessas operações.

A motivação é clara: em um transplante, cada minuto conta. Uma rota otimizada pode significar a diferença entre o sucesso e a falha de um procedimento. O projeto se relaciona diretamente com os conceitos de Teoria dos Grafos (representação da rede de ruas e cálculo de caminhos), Estrutura de Dados (armazenamento e manipulação do grafo e dos dados de localização) e Sistemas Distribuídos/Integração de APIs (uso de serviços externos como OpenRouteService para dados de tráfego e geocodificação).

👨‍💻 Tecnologias Utilizadas
As principais tecnologias e bibliotecas empregadas no desenvolvimento deste roteador são:

Python 3.x
Tkinter: Para a construção da interface gráfica do usuário (GUI).
Folium: Para a visualização interativa das rotas em mapas HTML.
Geopy: Para geocodificação de endereços (convertendo nomes de locais em coordenadas geográficas).
OSMnx: Para download, modelagem e análise da rede de ruas de Mogi das Cruzes a partir de dados do OpenStreetMap, e para encontrar os nós mais próximos.
NetworkX: Biblioteca de grafos utilizada para implementar o algoritmo de Dijkstra e encontrar o caminho mais curto na rede de ruas.
OpenRouteService (ORS): API utilizada para obter estimativas de tempo de viagem considerando o tráfego em tempo real (requer uma chave de API).
Pillow (PIL): Para manipulação de imagens (usado na tela de splash).
🗂️ Estrutura do Projeto
O projeto segue um padrão de arquitetura MVC (Model-View-Controller) para garantir modularidade, manutenibilidade e escalabilidade.

📦 mogi_caminhos_app
├── 📁 assets/               # Imagens e outros recursos (ex: logo.png)
│   └── logo.png
├── 📁 controller/
│   ├── __init__.py
│   └── app_controller.py   # Lógica principal do controlador, orquestra Model e View
├── 📁 model/
│   ├── __init__.py
│   ├── graph_manager.py    # Lógica de carregamento/gerenciamento do grafo OSMnx
│   ├── location_data.py    # Lógica de geocodificação e cache de coordenadas
│   └── route_calculator.py # Lógica de cálculo de rotas (Dijkstra, ORS)
├── 📁 view/
│   ├── __init__.py
│   ├── main_view.py        # Lógica da GUI principal
│   ├── splash_view.py      # Lógica da tela de splash
│   └── map_viewer.py       # Lógica de criação e exibição do mapa Folium
├── main.py                 # Ponto de entrada da aplicação
├── README.md
├── coordenadas_cache_v3.pkl  # Arquivo de cache gerado (não versionado)
└── mogi_das_cruzes_street_network.pkl # Grafo de ruas salvo (gerado após 1ª execução)
⚙️ Como Executar
✅ Rodando Localmente
Para configurar e executar o projeto em sua máquina local, siga os passos abaixo:

Clone o repositório:

Bash

git clone https://github.com/seu-usuario/seu-projeto.git # Substitua pelo seu repositório
cd mogi_caminhos_app
Crie e ative o ambiente virtual:
É altamente recomendável usar um ambiente virtual para gerenciar as dependências do projeto.

Bash

python -m venv venv
# No Windows:
venv\Scripts\activate
# No macOS/Linux:
source venv/bin/activate
Instale as dependências:
Você precisará instalar as bibliotecas Python listadas. Se você não tem um requirements.txt ainda, pode instalá-las manualmente ou criar um:

Bash

# Para criar um requirements.txt a partir do seu ambiente
pip freeze > requirements.txt
# Depois, instale as dependências:
pip install -r requirements.txt
Se você for criar o requirements.txt a partir do seu código, as principais bibliotecas seriam:
tkinter (geralmente já vem com Python), Pillow, folium, geopy, osmnx, networkx, openrouteservice.

Configure a Chave da API do OpenRouteService:
Edite o arquivo controller/app_controller.py e substitua 'SUA_API_KEY_AQUI' pela sua chave de API real do OpenRouteService. Você pode obter uma chave gratuita em: https://openrouteservice.org/sign-up

Python

# controller/app_controller.py
ORS_API_KEY = 'SUA_CHAVE_AQUI'
Execute a aplicação:

Bash

python main.py
Na primeira execução, o aplicativo baixará o grafo de ruas de Mogi das Cruzes, o que pode levar alguns minutos. Uma tela de splash será exibida durante esse processo.
📸 Demonstrações
(Aqui você deve incluir as capturas de tela/GIFs/vídeos do seu aplicativo em funcionamento)

Tela de Splash:
(Inserir imagem da tela de splash aqui)

Interface Principal:
(Inserir imagem da tela principal com os campos de seleção)

Exemplo de Rota Calculada:
(Inserir imagem do mapa Folium com uma rota desenhada)

Cálculo para o Hospital Mais Próximo:
(Opcional: print mostrando o resultado de "hospital mais próximo")

👥 Equipe
Nome	GitHub
[Cesar Luiz da Silva]	[Luizcs-Lab](https://github.com/Luizcs-lab/Projeto_Teoria_Grafos)
[Caio de Moura Camargo]	[Caio-Moura]

Exportar para as Planilhas
🧠 Disciplinas Envolvidas
Estrutura de Dados I: Utilização e manipulação de grafos (rede de ruas), caches e outras estruturas.
Teoria dos Grafos: Aplicação de algoritmos de busca de caminho mínimo (Dijkstra) na rede de ruas.
Sistemas Operacionais/Programação Concorrente: Uso de multi-threading para operações em segundo plano (cálculo de rota e carregamento do grafo) para manter a GUI responsiva.
Engenharia de Software: Aplicação do padrão de arquitetura MVC para organização e manutenção do código.
Redes de Computadores / Integração de APIs: Interação com APIs externas (OpenRouteService, Nominatim) para geocodificação e dados de tráfego.
🏫 Informações Acadêmicas
Universidade: Universidade Braz Cubas
Curso: Ciência da Computação
Semestre: 2 semestre
Período: noturno
Professora orientadora: Dra. Andréa Ono Sakai
Evento: Mostra de Tecnologia 1º Semestre de 2025
Local: Laboratório 12
Datas: 05 e 06 de junho de 2025
📄 Licença
MIT License — sinta-se à vontade para utilizar, estudar e adaptar este projeto.