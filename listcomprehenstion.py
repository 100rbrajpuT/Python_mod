#1. List Comprehension | Hackerrank Solution | Python


list1  = [1,2]
list2 = [3,4,5]

# posilble combinations--> [1,3][1,4][1,5][2,3][2,4][2,5]

newlist = [[x,y] for x in list1 for y in list2]
print(newlist)

#  *************
x= 1
y=1
z=1
n = 3

x1 = [p for p in range(x+1)]
y1 = [q for q in range(y+1)]
z1 = [r for r in range(z+1)]    

perm = [[i,j,k] for i in x1 for j in y1 for k in z1]
res = [l for l in perm if sum(l)!=n]
print(res)
    