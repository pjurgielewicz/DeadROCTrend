from ROOT import *
from copy import deepcopy
from rhapi import DEFAULT_URL, RhApi
import os

from config import *

gROOT.SetBatch() # don't pop up canvases
gStyle.SetOptStat()

gEnv.SetValue("Davix.GSI.UserCert", cert_file_path)
gEnv.SetValue("Davix.GSI.UserKey", key_file_path)

### CODING NAMES AND LIMITS

histogramNames = [histBaseInRootFile + "Layer_" + str(i) for i in range(1, 5)]
histogramNames.extend([histBaseInRootFile + "Ring_" + str(i) for i in range(1, 3)])
print(histogramNames)

histogramDictionaryList = { name : [] for name in histogramNames}

rocTable = [v * 16 for v in [96, 224, 352, 512, 44 * 6, 68 * 6]]

### DEFINITIONS

def GetRunNumbers(start, end):
  api = RhApi(DEFAULT_URL, debug = False)
        
  queryPieces = ["r.starttime between to_date('" + start + "', 'dd/mm/yyyy')",
                  "to_date('" + end + "', 'dd/mm/yyyy')",
                  "r.pixel_present = 1",
                  "r.tracker_present = 1",
                  "r.bpix_ready = 1",
                  "r.fpix_ready = 1",
                  "r.beam1_stable = 1", 
                  "r.beam2_stable = 1",
                  "r.run_test = 0" 
                  ]
  q = "select r.runnumber from runreg_tracker.runs r where " + " and ".join(queryPieces)
  print(q)
  
  p = {}
  qid = api.qid(q)

  print api.count(qid, p)
  
  runNumbers = api.json_all(q, p)
  runNumbers = [r[0] for r in runNumbers]
  runNumbers.sort()
  
  return runNumbers
  
########################################

def LinkGenerator(runNum):
  runNumStr = str(runNum)
  
  highStr = "000" + runNumStr[0:2] + "x"*4
  medStr = "000" + runNumStr[0:4] + "x"*2
  fileStr = fileBase + "000" + runNumStr + ".root"
  
  return urlBase + highStr + "/" + medStr + "/" + fileStr
  
########################################

def AppendHistograms(plots, name):
  total_bins = 0;
  total_range = 0;
  for plot in plots:
    total_range += int(plot.GetXaxis().GetXmax() * (plot.FindLastBinAbove(0.1) / float(plot.GetSize() - 2)))
    total_bins  += plot.FindLastBinAbove(0.1)#plot.GetSize() - 2 #

  merged = TH1F("Dead ROCs: " + name,"Dead ROCs: " + name, total_bins, 0, total_range);
  merged.GetXaxis().SetTitle("LS (x 10)")
  merged.GetYaxis().SetTitle("# dead ROCs")
  merged.SetStats(0)

  offset = 0;
  for plot in plots:
    last_idx = plot.FindLastBinAbove(0.1);

    for bin in range(0, last_idx):
      val = plot.GetBinContent(bin)
      idx = histogramNames.index(name)
      
      ### SKIP BIN IF IT IS HIGHER THAN 50% OF THE ASSOCIATED LAYER ROC CNT
      if val < rocTable[idx] * 0.5:
        merged.SetBinContent(bin+offset, val)
      else:
        merged.SetBinContent(bin+offset, 0)
    
    offset += last_idx;        
  return merged;
  
########################################
  
def StackHistograms(plots, name):
  stack = THStack("Dead ROCs: " + name, "Dead ROCs: " + name)
  
  for p in plots:
    stack.Add(p)
  
  return stack
  
########################################
  
def GetLabels(plots, realRuns, totalLabelNum = 25):
  totalLength = 0
  for plot in plots:
    totalLength += plot.FindLastBinAbove(0.1)
   
  levelEvery = totalLength / totalLabelNum
    
  currentLS = 0.0
  nextLevel = levelEvery / 2
  labelsDic = {}
  for i in range(len(realRuns)):
    plot = plots[i]
    run = realRuns[i]
    currentRunLength = plot.FindLastBinAbove(0.1)
    
    if currentLS + currentRunLength * 0.5 >= nextLevel:
      labelsDic.update({run : (currentLS + currentRunLength * 0.5) / totalLength})  
      nextLevel += levelEvery
      
    currentLS += currentRunLength
    
  return labelsDic
  
########################################
  
def PrintLabels(labelsDic):
  txt = TLatex()
  txt.SetNDC()
  txt.SetTextFont(1)
  txt.SetTextSize(0.025)
  txt.SetTextColor(1)
  txt.SetTextAlign(22)
  txt.SetTextAngle(90)
  
  for run in labelsDic:
    txt.DrawLatex(labelsDic[run] * 0.8 + 0.1, 0.8, str(run))
    
########################################
# TODO: tricky part    
def CreateLuminosityTrend(realRuns):
  minimum = min(realRuns)
  maximum = max(realRuns)
  
  api = RhApi(DEFAULT_URL, debug = False)
        
  queryPieces = ["r.runnumber >= :min",
                  "r.runnumber <= :max",
                  "r.pixel_present = 1",
                  "r.tracker_present = 1",
                  "r.bpix_ready = 1",
                  "r.fpix_ready = 1",
                  "r.beam1_stable = 1", 
                  "r.beam2_stable = 1",
                  "r.run_test = 0" 
                  ]
  q = "select r.runnumber, r.runlivelumi, r.duration from runreg_tracker.runs r where " + " and ".join(queryPieces) + " order by r.runnumber asc"
  print(q)
  
  p = {"min" : str(minimum),
       "max" : str(maximum)}
  
  runNumbers = api.json_all(q, p)
  
#######################################################################################################################################

### !DEFINITIONS

runNumbers = GetRunNumbers(dateStart, dateEnd)

print(runNumbers)

realRuns = []
for run in runNumbers: 
  theUrl = LinkGenerator(run)
  try:
    file = TFile.Open(theUrl)
    # file = TFile.Open("DQM_V0001_PixelPhase1_R000304366.root")
    
    if file.IsOpen():
      print("Success: %d" % (run))
      realRuns.append(run)
     
      baseRootDir = "DQMData/Run " + str(run) + "/PixelPhase1/Run summary"
      for o in file.Get(baseRootDir).GetListOfKeys():
        if o.GetName() in histogramNames:        
          histogramDictionaryList[o.GetName()].append(deepcopy(o.ReadObj())) 
           
      file.Close()
  except:
    print("Couldn't find: %d" % (run))

### PREPARE LABELS 
labelsDic = GetLabels(histogramDictionaryList[histogramNames[0]], realRuns)  
listOfSingleLayerMergedHistograms = []

if not os.path.exists(outputDir):
  os.system("mkdir " + outputDir)

# MERGE AND PRINT
for name in histogramNames:
  c = TCanvas(name, name, histWidth, histHeight)

  newObj = AppendHistograms(histogramDictionaryList[name], name)
  newObj.Draw()
  
  # PRINT RUN LABELS AT THE RIGHT POSITION
  PrintLabels(labelsDic)
  
  listOfSingleLayerMergedHistograms.append(deepcopy(newObj))

  # SAVE TO FILE
  c.Print(outputDir + name + "." + fileType)
  
# CREATE STACKED
stackedDictinary = { "Barrel" : listOfSingleLayerMergedHistograms[0:4],
                     "Endcap" : listOfSingleLayerMergedHistograms[4: ],
                     "Pixel"  : listOfSingleLayerMergedHistograms}

for name in stackedDictinary:                                       
  c = TCanvas(name, name, histWidth, histHeight)
  obj = StackHistograms(stackedDictinary[name], name)
  obj.Draw()
  
  # PRINT RUN LABELS AT THE RIGHT POSITION
  PrintLabels(labelsDic)
  
  obj.GetXaxis().SetTitle("LS (x 10)")
  obj.GetYaxis().SetTitle("# dead ROCs")
  
  c.Modified()
  
  c.Print(outputDir + name + "." + fileType)


    
   




