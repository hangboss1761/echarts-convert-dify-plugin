# Conversor de ECharts para Imagem

**Autor:** hangboss1761
**Versão:** 0.0.1
**Tipo:** tool
**Repositório:** <https://github.com/hangboss1761/echarts-convert-dify-plugin>

## Visão Geral

Conversor de ECharts para Imagem é um plugin poderoso do Dify que converte configurações ECharts em texto para imagens de alta qualidade. O plugin suporta processamento em lote, renderização concorrente e configuração flexível de formato de saída.

**Caso de Uso**: Perfeito para converter configurações de gráficos ECharts de strings markdown em imagens, então converter strings markdown completas para formatos docx/pdf (use o plugin `md_exporter`).

![usecase](../_assets/image.png)

Este plugin funciona completamente offline, com dependências externas zero.

> Versão do Echarts: 5.6.0

## Configuração

O Conversor de ECharts para Imagem fornece as seguintes opções de configuração:

### Parâmetros de Entrada

- **Conteúdo**: Texto contendo um ou mais blocos de código ````echarts```` com configurações JSON do ECharts (obrigatório)
- **Tipo de Imagem**: Formato de imagem de saída (`svg` - Apenas SVG)
- **Largura**: Largura do gráfico em pixels (100-4000, padrão: 800)
- **Altura**: Altura do gráfico em pixels (100-4000, padrão: 600)

### Opções Avançadas

- **Número de Workers**: Número de processos worker para renderização simultânea (1-4, padrão: 1)
  - **Recomendação**: Use 2-4 para gráficos complexos, 1 para gráficos simples
- **Mesclar Opções ECharts**: Opções adicionais do ECharts em formato JSON (opcional)

### ⚡ Guia de Performance de Concorrência

**Usar Concorrência** (2-4 workers):
- Gráficos complexos com grandes conjuntos de dados
- Visualizações multisséries
- Performance depende das capacidades do seu hardware

**Usar Sequencial** (não usar workers):
- Gráficos simples (barra, pizza, linha)
- Pequenos conjuntos de dados
- Renderização de único gráfico

**Nota**: Ganhos de performance variam baseados nas especificações do dispositivo e complexidade do gráfico.

## Desenvolvimento

### Configuração do Ambiente de Desenvolvimento

Copie `.env.example` para `.env` e preencha os valores.

```bash
# Instalar dependências Python
pip install -r requirements.txt

# Instalar dependências js-executor (apenas desenvolvimento)
cd js-executor
# Instalar Bun: <https://bun.sh/docs/installation>
# pule se já tiver instalado o Bun
bun install

# Executar em modo de desenvolvimento
python -m main

# Executar em modo de desenvolvimento com binário local, use bun run build:dev para build o binário local.
ECHARTS_CONVERT_LOCAL_PATH=./executables/echarts-convert-local python -m main

# Mais informações em GUIDE.md
```

**Nota:** Para implantação em produção no Dify, o plugin requer **dependências externas zero**. Todas as dependências de runtime JavaScript são empacotadas com o plugin, permitindo operação offline completa sem exigir chamadas de API externas ou conectividade com a internet.

Em seguida, adicione o plugin no fluxo de trabalho do Dify e teste-o.

## Exemplo de Uso

```markdown
# Gráfico de Exemplo

```echarts
{
  "title": {
    "text": "Gráfico de Exemplo"
  },
  "xAxis": {
    "type": "category",
    "data": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
  },
  "yAxis": {
    "type": "value"
  },
  "series": [{
    "data": [120, 200, 150, 80, 70, 110, 130],
    "type": "bar"
  }]
}
```
```

O plugin extrairá automaticamente a configuração ECharts e converterá para o formato de imagem especificado.

## 🤝 Contribuindo

Issues e Pull Requests são bem-vindos!

**Nota**: Este plugin é projetado especificamente para a plataforma Dify e requer ambiente Dify para funcionar.