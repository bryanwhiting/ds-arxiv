rmd_template = """
---
title: "Daily Articles"
description: |
  There are {n} articles published on {yesterday}.
author:
  - name: Bryan Whiting
    url: https://www.bryanwhiting.com
date: {date}
output:
  distill::distill_article:
    self_contained: false
---


```{{r setup, include=FALSE}}
knitr::opts_chunk$set(echo = FALSE)
```

"""