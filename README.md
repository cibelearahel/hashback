# Demonstração e Apresentação do HashBack DApp

## 1. Justificativa do Problema e Uso de Blockchain
- **Problema Real dos Programas Tradicionais:**
  - **Falta de transparência e auditoria:** Pontos podem expirar ou sumir sem rastreabilidade.
  - **Gasto Duplo (Double Spending):** Risco de usar o mesmo voucher ou pontuação em dois canais concorrentes.
  - **Centralização:** Parceiros comerciais dependem de conciliações lentas e bancos de dados relacionais centralizados vulneráveis.
- **Por que Blockchain resolve:**
  - **Ledger Imutável:** Blocos encadeados por SHA-256 e timestamps imutáveis.
  - **Contrato Inteligente:** Execução determinística de regras de negócio. Impede gasto duplo atômico (`saldo < valor = rejeição`).
  - **Criptografia Asimétrica:** Assinaturas digitais ECDSA secp256k1 para garantir que apenas o legítimo proprietário autoriza a movimentação.

---

## 2. O que fica na Blockchain vs. O que fica fora
| Dado | Onde fica? | Motivo |
| :--- | :--- | :--- |
| **Índice do Bloco & Timestamp** | **Na Blockchain** | Garantia cronológica imutável. |
| **Hash Anterior & Hash Atual** | **Na Blockchain** | Encadeamento e integridade criptográfica. |
| **Transações (MINT, TRANSFER, REDEEM)** | **Na Blockchain** | Histórico imutável de todas as ações assinadas. |
| **Assinatura Digital ECDSA & Nonce** | **Na Blockchain** | Comprovação de autoria e prevenção contra replay attack. |
| **Saldos Atuais dos Clientes** | **World State (Contrato)** | Calculados deterministicamente pela soma/subtração dos blocos. |
| **Vouchers Ativos e Catálogo** | **World State (Contrato)** | Controle de status e regras de queima de tokens. |

---

## 3. Rodando a Aplicação

O servidor já está ativo em: **`http://localhost:8000`**

### Passo 1: Apresentar a Blockchain em Execução
1. Abra `http://localhost:8000` no seu navegador.
2. Mostre o badge superior: **"Blockchain Ativa & Íntegra"**.
3. Na seção inferior, aponte para o **Bloco #0 (Bloco Gênesis)** com seu hash SHA-256 e `previous_hash` nulo.

### Passo 2: Realizar uma Operação Válida (Emissão de Pontos)
1. Certifique-se de que a conta selecionada no topo é **Loja Parceira (Oficial)**.
2. Na aba **"Emitir Pontos (Loja)"**:
   - Destinatário: **Alice**.
   - Quantidade: **150** pontos.
   - Clique em **"Emitir Pontos & Criar Bloco"**.
3. **Resultado:**
   - O banner verde de sucesso surge.
   - O **Bloco #1** aparece instantaneamente na linha do tempo com a transação `MINT 150 HBC` assinada.

### Passo 3: Consultar Registro e Mostrar Alteração de Estado no Contrato
1. No seletor de contas no topo, clique no perfil **Alice**.
2. Mostre que o saldo da Alice foi atualizado para **150 HBC** e o Nonce foi preservado.
3. No **Catálogo de Recompensas** à direita, clique em **"Resgatar"** no item *"Cupom de R$ 20 OFF"* (custa 100 pontos).
4. **Resultado:**
   - O saldo da Alice é reduzido para **50 HBC**.
   - Um novo **Bloco #2** do tipo `REDEEM` é selado na Blockchain.
   - O voucher imutável (ex: `HASH-REW-1-...`) é gerado no contrato e exibido na lista *"Meus Vouchers Emitidos pelo Contrato"*.

### Passo 4: Demonstrar a Rejeição de Operação Inválida ou Sem Permissão
1. Ainda na conta da **Alice** (que agora possui apenas 50 pontos):
   - Vá na aba **"Auditoria & Testes de Rejeição"**.
   - Clique em **"Simular Gasto Duplo"**:
     - *Tentativa de gastar mais pontos do que possui.*
     - **Resultado:** O banner vermelho exibe a rejeição imediata do Contrato: `[GASTO DUPLO BLOQUEADO]: Rejeitada pelo Contrato: Tentativa de gasto duplo ou saldo insuficiente...` e **nenhum bloco adicional é criado**.
   - Clique em **"Simular Emissão Não Autorizada"**:
     - *Cliente Alice tentando emitir pontos para si mesma.*
     - **Resultado:** O contrato rejeita: `[CONTRATO REJEITOU]: Rejeitada pelo Contrato: Apenas lojas parceiras autorizadas podem emitir pontos...`.

---

## 4. Como Rodar Novamente se Necessário
```bash
python run.py
```
Acesse no navegador: `http://localhost:8000`
Para rodar a suíte de testes do contrato:
```bash
python test_contract.py
```
