# Como rodar somente o frontend

Este passo sobe apenas a interface web do QuantVision. Não é necessário iniciar o backend local se você for usar a API AWS já configurada no frontend.

## Pré-requisito

- Ter Python instalado na máquina.

## Subir o frontend

No PowerShell, execute:

```powershell
cd "C:\Users\Henrique Yuji\Desktop\Otimizador\frontend"
python -m http.server 8080
```

Depois, abra no navegador:

```text
http://localhost:8080
```

## API usada pelo frontend

O frontend já vem configurado com esta API base:

```text
https://rqdwpiwn5b.execute-api.us-east-2.amazonaws.com/prod
```

Se precisar trocar a API, altere o campo `API` na barra superior da tela ou na página de configurações do próprio frontend.

## Se a porta 8080 estiver ocupada

Use outra porta, por exemplo:

```powershell
cd "C:\Users\Henrique Yuji\Desktop\Otimizador\frontend"
python -m http.server 8081
```

E acesse:

```text
http://localhost:8081
```

