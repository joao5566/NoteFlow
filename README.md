# Calendário Interativo com Notas

Um aplicativo de calendário interativo que permite gerenciar notas, tarefas, lembretes, um sistema de gamificação e outras funcionalidades.

## Recursos

- **Gerenciamento de Notas**: Adicione, edite e exclua notas associadas a datas.
- **Tarefas e Kanban**: Organização de tarefas usando um sistema Kanban.
- **Estatísticas**: Exibição de gráficos e relatórios sobre notas e produtividade.
- **Gamificação**: Um sistema de gamificação para incentivar hábitos produtivos.
- **Editor de Texto**: Um editor de anotações avançado com busca e substituição.
- **Exportação e Importação**: Possibilidade de exportar notas para PDF e importar/exportar dados.
- **Tema Personalizável**: Ajuste as cores do tema para melhor experiência de uso.

## Requisitos

- Python 3.x
- PyQt5
- SQLite3
- OpenPyxl (para exportação de planilhas)

## Instalação

1. Clone o repositório:
   ```sh
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio
   ```
2. Instale as dependências:
   ```sh
   pip install -r requirements.txt
   ```
3. Execute o programa:
   ```sh
   python main.py
   ```

## Estrutura do Projeto

```
.
├── main.py                 # Arquivo principal
├── persistence_module.py   # Gerenciamento do banco de dados
├── notes_table_module.py   # Módulo de notas
├── kanban_tab.py           # Aba de tarefas Kanban
├── stats_module.py         # Módulo de estatísticas
├── day_notes_dialog.py     # Gerenciamento de notas por data
├── mind_map_tab.py         # Editor de texto
├── motivation_module.py    # Mensagens motivacionais
├── theme_module.py         # Configuração de tema
├── simple_excel.py         # Exportação e manipulação de planilhas
└── requirements.txt        # Dependências do projeto
```

## Uso

- **Adicionar uma Nota**: Clique no dia desejado e adicione uma nova nota.
- **Gerenciar Tarefas**: Utilize a aba Kanban para organizar suas tarefas.
- **Visualizar Estatísticas**: Acesse a aba de estatísticas para acompanhar seu progresso.
- **Personalizar o Tema**: Ajuste as cores e aparência no menu de configurações.
- **Gamificação**: Acompanhe seu progresso com o sistema de recompensas integrado.

## Contribuição

Se quiser contribuir para o projeto, siga os passos:
1. Faça um Fork do repositório.
2. Crie uma branch para sua funcionalidade:
   ```sh
   git checkout -b minha-nova-funcionalidade
   ```
3. Faça as alterações e commit:
   ```sh
   git commit -m "Adiciona nova funcionalidade"
   ```
4. Envie para o repositório:
   ```sh
   git push origin minha-nova-funcionalidade
   ```
5. Abra um Pull Request.

## Licença

Este projeto está licenciado sob a licença MIT.

