#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 10:44:31 2023

@author: danakoeppe
"""
from multiprocessing import Process
def func1():
    for i in range(500):
        pass
    print("func1 done")
    
def func2():
    for i in range(500):
        pass
    print("func2 done")
    
def runInParallel(*fns):
  proc = []
  for fn in fns:
    p = Process(target=fn)
    p.start()
    proc.append(p)
  for p in proc:
    p.join()



if __name__ == '__main__':
  p1 = Process(target=func1)
  p1.start()
  p2 = Process(target=func2)
  p2.start()
  p1.join()
  p2.join()
  
  
runInParallel(func1, func2)

