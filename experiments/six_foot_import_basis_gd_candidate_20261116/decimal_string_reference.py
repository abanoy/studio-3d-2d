"""Independent bounded integer/string oracle for the unrun GDScript algorithm."""
def rounded_ratio(numerator,denominator):
    assert isinstance(numerator,str)and isinstance(denominator,str)
    assert 0<len(numerator)<=192 and 0<len(denominator)<=192
    assert numerator.isascii()and numerator.isdigit()and denominator.isascii()and denominator.isdigit()
    n,d=int(numerator),int(denominator)
    assert n>0 and d>0
    whole,remainder=divmod(n,d)
    coefficient=str(whole)
    exponent=len(coefficient)-1
    if whole==0:
        coefficient='';exponent=-1
        while not coefficient:
            digit,remainder=divmod(remainder*10,d)
            if digit:coefficient=str(digit)
            else:exponent-=1
    while len(coefficient)<51 and remainder:
        digit,remainder=divmod(remainder*10,d);coefficient+=str(digit)
    if len(coefficient)>50:
        digit=int(coefficient[50]);tail=remainder!=0 or any(c!='0'for c in coefficient[51:])
        coefficient=coefficient[:50]
        if digit>5 or digit==5 and(tail or int(coefficient[-1])%2):coefficient=str(int(coefficient)+1)
        if len(coefficient)>50:coefficient=coefficient[:50];exponent+=1
    point=exponent+1
    if point<=0:output='0.'+'0'*(-point)+coefficient
    elif point>=len(coefficient):output=coefficient+'0'*(point-len(coefficient))
    else:output=coefficient[:point]+'.'+coefficient[point:]
    return output.rstrip('0').rstrip('.')if'.'in output else output
