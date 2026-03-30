__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__license__    = ""
__version__    = "2.32"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

''' '''
import time

import ROOT

import constants as myconstants

###############################################################################
class HmpGraph():
    """
    Worker thread that performs a task in the background.
    """
    def __init__(   self, 
                    server_name : str,
                    max_time : int = 60,
                    def_dict={  'V1': 2.8, 'A1': 2.5, 
                                'V2': 2.2, 'A2': 2.9, 
                                'V3': 2.8, 'A3': 2.5, 
                                'V4': 2.2, 'A4': 3.0}):

        self.server_name = server_name
        self.meas_time   = max_time
        self.sett_dict   = def_dict

        self.h2D_V = None
        self.h2D_I = None

        self.InitRoot()
        self.draw_all()

        self.values = [None] * 16

    #==========================================================================
    def __del__(self):
        return

    #==========================================================================
    def InitRoot(self):

        ROOT.gStyle.SetOptStat(0)
        ROOT.gStyle.SetOptFit(1)

        ## [A1.8 A1.2 B1.8 B1.2]
        # mark = [20,21,22,23] # full symbols
        mark = [24,25,26,32] # open symbols

        line_width = [4, 2, 4, 2] #

        #          [ F E B __ A               ] [ F E B __ B ]
        markColr = [ROOT.kBlue-7, ROOT.kBlue+1, ROOT.kRed-7, ROOT.kRed+1] #
        lineColr = [ROOT.kBlue-7, ROOT.kBlue+1, ROOT.kRed-7, ROOT.kRed+1] # 

        self.cCanvas = ROOT.TCanvas( f'c{self.server_name}', 
                                        f'c{self.server_name}', 
                                        2560, 0, 1000, 700 ) # 5120/2=2560 1440
        self.cCanvas.Divide(1,2,.001,.001)
        
        self.cCanvas.GetPad(1).SetBottomMargin(0.005)
        self.cCanvas.GetPad(1).SetRightMargin(0.005)
        self.cCanvas.GetPad(1).SetTickx(1)

        self.cCanvas.GetPad(2).SetTopMargin(0)
        self.cCanvas.GetPad(2).SetRightMargin(0.005)
        self.cCanvas.GetPad(2).SetTickx(1)

        self.init_2d_histo()

        # voltage -------------------------------------------------------------
        self.cCanvas.cd(1)
        VoltageLineWidth = 10
        self.lV18 = ROOT.TLine(0, self.sett_dict['V1'], self.meas_time, self.sett_dict['V1'])
        self.lV18.SetHorizontal(1)
        self.lV18.SetLineStyle(3)
        self.lV18.SetLineColor(lineColr[1])
        self.lV18.SetLineWidth(VoltageLineWidth)

        self.lV12 = ROOT.TLine(0, self.sett_dict['V2'], self.meas_time, self.sett_dict['V2'])
        self.lV12.SetHorizontal(1)
        self.lV12.SetLineStyle(3)
        self.lV12.SetLineColor(lineColr[0])
        self.lV12.SetLineWidth(VoltageLineWidth)

        # current -------------------------------------------------------------
        self.cCanvas.cd(2)

        CurrentLineWidth = 20
        self.lICSA = ROOT.TLine(0, self.sett_dict['A1'], self.meas_time, self.sett_dict['A1'])
        self.lICSA.SetHorizontal(1)
        self.lICSA.SetLineStyle(3)
        self.lICSA.SetLineColor(lineColr[0])
        self.lICSA.SetLineWidth(CurrentLineWidth)

        self.lIVDA = ROOT.TLine(0, self.sett_dict['A2'], self.meas_time, self.sett_dict['A2'])
        self.lIVDA.SetHorizontal(1)
        self.lIVDA.SetLineStyle(3)
        self.lIVDA.SetLineColor(lineColr[1])
        self.lIVDA.SetLineWidth(CurrentLineWidth)

        self.lIVDD = ROOT.TLine(0, self.sett_dict['A3'], self.meas_time, self.sett_dict['A3'])
        self.lIVDD.SetHorizontal(1)
        self.lIVDD.SetLineStyle(3)
        self.lIVDD.SetLineColor(lineColr[2])
        self.lIVDD.SetLineWidth(CurrentLineWidth)

        ## graphs
        self.grCh1V = ROOT.TGraph(1) # 1.8V
        self.grCh1V.SetName("grCh1V")
        self.grCh1V.SetMarkerStyle(mark[0])
        self.grCh1V.SetMarkerColor(markColr[0])
        self.grCh1V.SetLineColor(markColr[0])
        self.grCh1V.SetLineWidth(line_width[0])
        self.grCh1V.SetLineStyle(2)
        self.grCh1V.SetMarkerSize(1)

        self.grCh2V = ROOT.TGraph(1)
        self.grCh2V.SetName("grCh2V")
        self.grCh2V.SetMarkerStyle(mark[1])
        self.grCh2V.SetMarkerColor(markColr[1])
        self.grCh2V.SetLineColor(markColr[1])
        self.grCh2V.SetLineWidth(line_width[1])
        self.grCh2V.SetMarkerSize(1)

        self.grCh3V = ROOT.TGraph(1)
        self.grCh3V.SetName("grCh3V")
        self.grCh3V.SetMarkerStyle(mark[2])
        self.grCh3V.SetMarkerColor(markColr[2])
        self.grCh3V.SetLineColor(markColr[2])
        self.grCh3V.SetLineWidth(line_width[2])
        self.grCh3V.SetLineStyle(2)
        self.grCh3V.SetMarkerSize(1)

        self.grCh4V = ROOT.TGraph(1)
        self.grCh4V.SetName("grCh4V")
        self.grCh4V.SetMarkerStyle(mark[3])
        self.grCh4V.SetMarkerColor(markColr[3])
        self.grCh4V.SetLineColor(markColr[3])
        self.grCh4V.SetLineWidth(line_width[3])
        self.grCh4V.SetMarkerSize(1)

        # current -------------------------------------------------------------
        self.grCh1I = ROOT.TGraph(1)
        self.grCh1I.SetName("grCh1I")
        self.grCh1I.SetMarkerStyle(mark[0])
        self.grCh1I.SetMarkerColor(markColr[0])
        self.grCh1I.SetLineColor(markColr[0])
        self.grCh1I.SetLineWidth(line_width[0])
        self.grCh1I.SetLineStyle(2)
        self.grCh1I.SetMarkerSize(1)

        self.grCh2I = ROOT.TGraph(1)
        self.grCh2I.SetName("grCh2I")
        self.grCh2I.SetMarkerStyle(mark[1])
        self.grCh2I.SetMarkerColor(markColr[1])
        self.grCh2I.SetLineColor(markColr[1])
        self.grCh2I.SetLineWidth(line_width[1])
        self.grCh2I.SetMarkerSize(1)

        self.grCh3I = ROOT.TGraph(1)
        self.grCh3I.SetName("grCh3I")
        self.grCh3I.SetMarkerStyle(mark[2])
        self.grCh3I.SetMarkerColor(markColr[2])
        self.grCh3I.SetLineColor(markColr[2])
        self.grCh3I.SetLineWidth(line_width[2])
        self.grCh3I.SetLineStyle(2)
        self.grCh3I.SetMarkerSize(1)

        self.grCh4I = ROOT.TGraph(1)
        self.grCh4I.SetName("grCh4I")
        self.grCh4I.SetMarkerStyle(mark[3])
        self.grCh4I.SetMarkerColor(markColr[3])
        self.grCh4I.SetLineColor(markColr[3])
        self.grCh4I.SetLineWidth(line_width[3])
        self.grCh4I.SetMarkerSize(1)


        self.cCanvas.cd(1)
        xx1 = 0.001
        yy1 = 0.2
        xx2 = xx1+0.07
        yy2 = yy1+0.4 
        self.legend_1 = ROOT.TLegend( xx1, yy1, xx2, yy2)
        self.legend_1.SetNColumns(1)
        self.legend_1.SetFillStyle(0)
        self.legend_1.AddEntry(self.grCh1V, f"{self.sett_dict['N1']}", "eL")
        self.legend_1.AddEntry(self.grCh2V, f"{self.sett_dict['N2']}", "eL")
        self.legend_1.AddEntry(self.grCh3V, f"{self.sett_dict['N3']}", "eL")
        self.legend_1.AddEntry(self.grCh4V, f"{self.sett_dict['N4']}", "eL")

        self.cCanvas.cd(2)
        self.legend_2 = ROOT.TLegend( xx1, yy1+0.1, xx2, yy2+0.1)
        self.legend_2.SetNColumns(1)
        self.legend_2.SetFillStyle(0)
        self.legend_2.AddEntry(self.grCh1I, f"{self.sett_dict['N1']}", "eL")
        self.legend_2.AddEntry(self.grCh2I, f"{self.sett_dict['N2']}", "eL")
        self.legend_2.AddEntry(self.grCh3I, f"{self.sett_dict['N3']}", "eL")
        self.legend_2.AddEntry(self.grCh4I, f"{self.sett_dict['N4']}", "eL")

    #==========================================================================
    def init_2d_histo(self):

        self.time_start = time.time()
        self.time_stop  = self.time_start + myconstants.MAX_TIME

        if self.h2D_V:
            self.h2D_V.Delete()
        self.h2D_V = ROOT.TH2D( "h2D_V", 
                                f";Measurement time [s];Voltage [V]", 
                                1000, (self.time_start-10), (self.time_stop+10), 
                                1000, -1, 5)
        self.h2D_V.GetXaxis().SetTimeDisplay(1)
        self.h2D_V.GetXaxis().SetTimeFormat("%H:%M:%S")
        self.h2D_V.GetYaxis().SetRangeUser(-0.1, 3.2)

        if self.h2D_I:
            self.h2D_I.Delete()
        self.h2D_I = ROOT.TH2D( "h2D_I", 
                                ";Measurement time [s];Current [A]", 
                                1000, (self.time_start-10), (self.time_stop+10),  
                                1000, -1, 10)
        self.h2D_I.GetXaxis().SetTimeDisplay(1)
        self.h2D_I.GetXaxis().SetTimeFormat("%H:%M:%S")
        self.h2D_I.GetYaxis().SetRangeUser( -0.1, 3.2)

    #==========================================================================
    def draw_all(self):

        self.cCanvas.cd(1)
        self.h2D_V.GetXaxis().SetRangeUser(-1, self.meas_time)
        self.h2D_V.Draw()
        self.lV12.SetX2(self.meas_time-1)
        self.lV12.Draw("same")
        self.lV18.SetX2(self.meas_time-1)
        self.lV18.Draw("same")

        self.grCh1V.Draw("same L")
        self.grCh2V.Draw("same L")
        self.grCh3V.Draw("same L")
        self.grCh4V.Draw("same L")

        self.legend_1.Draw("same")


        self.cCanvas.cd(2)
        self.h2D_I.GetXaxis().SetRangeUser(-1, self.meas_time)
        self.h2D_I.Draw()

        self.lICSA.SetX2(self.meas_time-1)
        self.lICSA.Draw("same")

        self.lIVDA.SetX2(self.meas_time-1)
        self.lIVDA.Draw("same")

        self.lIVDD.SetX2(self.meas_time-1)
        self.lIVDD.Draw("same")

        self.grCh1I.Draw("same L")
        self.grCh2I.Draw("same L")
        self.grCh3I.Draw("same L")
        self.grCh4I.Draw("same L")

        self.legend_2.Draw("same")

        self.cCanvas.Update()


    #==========================================================================
    def draw_graphs(self):
        self.cCanvas.Draw()
        self.cCanvas.Update()

    #==========================================================================
    def FillGraphs(self, HMPtime, HMPdata): 
        
        self.grCh1V.SetPoint(self.grCh1V.GetN(), HMPtime, float(HMPdata[0]))
        self.grCh1I.SetPoint(self.grCh1I.GetN(), HMPtime, float(HMPdata[1]))
        self.grCh2V.SetPoint(self.grCh2V.GetN(), HMPtime, float(HMPdata[2]))
        self.grCh2I.SetPoint(self.grCh2I.GetN(), HMPtime, float(HMPdata[3]))
        self.grCh3V.SetPoint(self.grCh3V.GetN(), HMPtime, float(HMPdata[4]))
        self.grCh3I.SetPoint(self.grCh3I.GetN(), HMPtime, float(HMPdata[5]))
        self.grCh4V.SetPoint(self.grCh4V.GetN(), HMPtime, float(HMPdata[6]))
        self.grCh4I.SetPoint(self.grCh4I.GetN(), HMPtime, float(HMPdata[7]))

    #==========================================================================
    def reset_graphs(self):

        self.reset_graph(self.grCh1V)
        self.reset_graph(self.grCh2V)
        self.reset_graph(self.grCh3V)
        self.reset_graph(self.grCh4V)

        self.reset_graph(self.grCh1I)
        self.reset_graph(self.grCh2I)
        self.reset_graph(self.grCh3I)
        self.reset_graph(self.grCh4I)

        self.init_2d_histo()
        self.draw_all()
        self.draw_graphs()
    
    #==========================================================================
    def reset_graph(self, graph):
        graph.Set(1) # to avoid -->Error in <TGraphPainter::PaintGraph>: illegal number of points (0)

    #==========================================================================
    def save_canvas(self, filename='report/HMP_IV_vs_t'):

        self.draw_all()
        self.cCanvas.SaveAs(filename+".root")
        self.cCanvas.SaveAs(filename+".png")
