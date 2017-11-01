# DeadROCsByLS tool
## What it does?
The tool creates trends of dead ROCs in runs that were taken between specified dates. Besides lumisection trend you also have the hint which run it was with run labels on the top of the plot.

The tool is also capable of stacking single layer/ring plots to create whole Barrel, Pixel and Tracker trend.

## Configuration and running

You need to modify ```config.py```:
1. You need to have a decrypted version of your Grid Certificate Private Key. [Here is the tutorial how to do it](https://support.citrix.com/article/CTX122930)
2. Modify ```cert_file_path``` and ```key_file_path``` so that they point to your certificate and private key.
3. Set the range of dates ```dateStart```, ```dateEnd```
4. As an option you can change the size of output plots(```histWidth```, ```histHeight```), output directory(```outputDir```) and desired output file type(```fileType```)

Then you need to run it: 
```python main.py``` and wait for the results.

## It is not working
First and above all most important: make sure your private key is decrypted and you have the correct path in ```config.py```.

Second very common reason is that Run Registry service is off or data in ```"https://cmsweb.cern.ch/dqm/online/data/browse/Original/"``` became inaccessible. Waiting for some time helps.