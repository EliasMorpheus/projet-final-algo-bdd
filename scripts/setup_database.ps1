$mysql = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
$envValues = Get-Content .env | Where-Object { $_ -match "=" } | ConvertFrom-StringData
$hostName = $envValues.DB_HOST
$port = $envValues.DB_PORT
$user = $envValues.DB_USER
$password = $envValues.DB_PASSWORD
$database = $envValues.DB_NAME

Get-Content sql\01_create_database.sql | & $mysql -h $hostName -P $port -u $user "-p$password"
Get-Content sql\02_insert_data.sql | & $mysql -h $hostName -P $port -u $user "-p$password" $database
Get-Content sql\04_views_functions.sql | & $mysql -h $hostName -P $port -u $user "-p$password" $database
python python\pipeline.py
