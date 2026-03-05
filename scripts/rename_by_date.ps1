# rename_by_date.ps1 - Переименование PDF по дате создания
param(
    [Parameter(Mandatory=$true)]
    [string]$FolderPath
)

$files = Get-ChildItem -Path $FolderPath -Filter "*.pdf" | Sort-Object CreationTime

$counter = 1
foreach ($file in $files) {
    $date = $file.CreationTime
    $newName = $date.ToString("yyyy-MM-dd") + ".pdf"
    
    # Если такое имя уже есть, добавляем номер
    $fullNewPath = Join-Path $FolderPath $newName
    $finalName = $newName
    $i = 1
    while (Test-Path $fullNewPath) {
        $finalName = $date.ToString("yyyy-MM-dd") + "_$i.pdf"
        $fullNewPath = Join-Path $FolderPath $finalName
        $i++
    }
    
    Write-Host "$($file.Name) → $finalName"
    Rename-Item -Path $file.FullName -NewName $finalName
    $counter++
}

Write-Host "✅ Переименовано $counter файлов"
