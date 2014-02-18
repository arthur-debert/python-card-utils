import cardutils

cctest = "4408 0412 3456 7893"
cc = cardutils.analyse(cctest)
print cc

for i in range(100):
    rc = cardutils.randomCard()

    print rc
