# Demo del protocolo de sockets (puerto 6061). No es HTTP, por eso no sirve REST Client.
#
# Uso:
#   .\socket-demo.ps1 -HostName IP_EC2 -Comando '{get:autores}'
#   .\socket-demo.ps1 -HostName IP_EC2 -Comando '{insert:{"tabla":"autores","nombre":"Euler","nacionalidad":"francia"}}'
# (IP_EC2 = IP publica de tu instancia; no la escribas en el repo)

param(
    [string]$HostName = "localhost",
    [int]$Port = 6061,
    [Parameter(Mandatory=$true)][string]$Comando
)

# Abrir conexion TCP directa al puerto del socket
$cliente = New-Object System.Net.Sockets.TcpClient($HostName, $Port)
$stream  = $cliente.GetStream()

# Mandar el comando como texto plano
$writer = New-Object System.IO.StreamWriter($stream)
$writer.AutoFlush = $true
$writer.WriteLine($Comando)

# Leer la respuesta (una linea de JSON)
$reader = New-Object System.IO.StreamReader($stream)
$respuesta = $reader.ReadLine()

$cliente.Close()

Write-Host ">> $Comando" -ForegroundColor DarkGray
Write-Host $respuesta -ForegroundColor Green
