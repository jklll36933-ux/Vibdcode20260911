#함수 정의
def add(a,b):
    return a + b

#함수 호출
result = add(3, 5)
print("The result is:", result)

#배열
lst = ["사과", "바나나", "체리"]
print(len(lst))  # 배열의 길이 출력

for fruit in lst:
    print(fruit)  # 배열의 각 요소 출력

lst.append("포도")  # 배열에 요소 추가
print(lst)  # 배열 출력

lst.remove("바나나")  # 배열에서 요소 제거
print(lst)  # 배열 출력

#tuple은 한방에 입력과 출력을 하는 배열형태
tp = (100, 200, 300)
print(len(tp))  # 튜플의 길이 출력
print(type(tp))  # 튜플의 타입 출력
for num in tp:
    print(num)  # 튜플의 각 요소 출력

#함수
def times(a, b):
    return a+b, a*b

#함수호출
result = times(3, 5)
print("The result is:", result)  # 튜플 형태로 반환된 결과 출력