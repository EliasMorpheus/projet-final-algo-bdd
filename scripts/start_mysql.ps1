$mysqlBin = "C:\Program Files\MySQL\MySQL Server 8.0\bin"
$dataDir = "C:\Users\mouel\mysql-projet-final-data"
$errorLog = "C:\Users\mouel\mysql-projet-final-error.log"
$envValues = Get-Content .env | Where-Object { $_ -match "=" } | ConvertFrom-StringData
$dbUser = $envValues.DB_USER
$dbPassword = $envValues.DB_PASSWORD

$isRunning = netstat -ano | Select-String ":3307"
if ($isRunning) {
    Write-Host "MySQL is already listening on 127.0.0.1:3307"
    exit 0
}

Start-Process `
    -FilePath "$mysqlBin\mysqld.exe" `
    -ArgumentList @("--datadir=$dataDir", "--port=3307", "--bind-address=127.0.0.1", "--mysqlx=0", "--console") `
    -WorkingDirectory $dataDir `
    -WindowStyle Hidden `
    -RedirectStandardError $errorLog

Start-Sleep -Seconds 5
& "$mysqlBin\mysqladmin.exe" -h 127.0.0.1 -P 3307 -u $dbUser "-p$dbPassword" ping
