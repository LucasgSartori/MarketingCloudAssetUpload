# MarketingCloudAssetUpload
Upload assets to Salesforce Marketing Cloud/Carregar arquivos para o marketing cloud
-------Portugues-------
Upload assets to marketing cloud em python.
Esse código nasceu da necessidade de realizar uploads de assets que compõem campanhas de marketing
para o marketing cloud.
O código monitora utilizando o pacote o watchdog uma pasta ou um conjunto de pastas e verifica dentro do arquivo json qual pasta está relacionada a qual
ID de pasta do salesforce marketing cloud está relacionada.
A estrutura do arquivo deve seguir o seguinte padrão.

C:\Arquivos_assets\
 ├── Pasta1\
 │    └── nova_imagem.jpg
 ├── Pasta2\
 │    └── nova_imagem.jpg
 ├── Pasta3\
 │    └── nova_imagem.jpg
 └── pasta_map.json

Na pasta também deve conter um arquivo json com o nome pasta_map.json que seguirá o seguinte padrão:
{
  "Pasta1": "ID da pasta destino no MKTC",
  "Pasta2": "ID da pasta destino no MKTC",
  "Pasta3": "ID da pasta destino no MKTC",
  "Pasta4": "ID da pasta destino no MKTC",
  "Pasta5": "ID da pasta destino no MKTC"
}

Ele irá orientar para qual pasta o arquivo deve ir para o marketing cloud com base na pasta do qual o arquivo foi colocado.

-------English-------
Upload assets to marketing cloud in Python.
This code arose from the need to upload assets that make up marketing campaigns to the marketing cloud.
The code monitors a folder or set of folders using the watchdog package and checks within the JSON file which folder is related to which Salesforce Marketing Cloud folder ID.
The file structure should follow the following pattern.

C:\Archive_assets\
 ├── Folder1\
 │    └── new_image.jpg
 ├── Folder2\
 │    └── new_image.jpg
 ├── Folder3\
 │    └── new_image.jpg
 |    └── new_archive.pdf
 └── pasta_map.json

 The folder should also contain a JSON file named folder_map.json that follows this pattern:
{
"Folder1": "Destination folder ID in MKTC",
"Folder2": "Destination folder ID in MKTC",
"Folder3": "Destination folder ID in MKTC",
"Folder4": "Destination folder ID in MKTC",
"Folder5": "Destination folder ID in MKTC"
}
It will guide you to the correct folder where the file should be moved to the marketing cloud, based on the folder where the file was placed.
