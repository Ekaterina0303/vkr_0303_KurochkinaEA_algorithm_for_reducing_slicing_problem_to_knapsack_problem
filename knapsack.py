import random
from math import ceil
from itertools import islice


def get_area_value(list_objects):
    area = [object for object in list_objects]
    value = [object for object in list_objects]
    return area, value


def delete_used_objects(list_objects, used_objects):
    list_removed_objects = []
    for item in used_objects:
        list_removed_objects.append(item[0])
        list_objects.remove(item[0])
    return list_objects


def knapsack(w, area, value):
    n = len(value)
    V = [[0 for a in range(w + 1)] for i in range(n + 1)]
    for i in range(n + 1):
        for a in range(w + 1):
            if i == 0 or a == 0:
                V[i][a] = 0
            elif area[i - 1] <= a:
                V[i][a] = max(value[i - 1] + V[i - 1][a - area[i - 1]], V[i - 1][a])
            else:
                V[i][a] = V[i - 1][a]
    res = V[n][w]
    a = w
    items_list = []
    for i in range(n, 0, -1):
        if res <= 0:
            break
        if res == V[i - 1][a]:
            continue
        else:
            items_list.append((area[i - 1], value[i - 1]))
            res -= value[i - 1]
            a -= area[i - 1]
    return items_list


def reduction(m, n, list_objects):
    result = []
    for i in range(m):
        area, value = get_area_value(list_objects)
        if area is None or value is None:
            break
        if len(area) == 0 or value is None:
            break
        knapsack_list = knapsack(n, area, value)
        ans = [item[0] for item in knapsack_list]
        print("Карта раскроя {0}: {1}".format(i+1, ans))
        result.append(sum([item[0] for item in knapsack_list]))
        list_objects = delete_used_objects(list_objects, knapsack_list)
    return result


def print_line(n, array):
    for i in range(ceil(len(array) / n)):
        print(*array[i*n:(i+1)*n])


if __name__ == '__main__':
    list_objects = [random.randrange(100, 999) for i in range(1500)]
    # dict_objects = {"1380":22, "1520":25, "1560":12, "1710":14, "1820":18, "1880":18, "1930":20, "2000":10, "2050":12, "2100":14, "2140":16, "2150":18, "2200":20}
    # dict_objects = {"1380":22}
    # list_objects = [1380, 1520, 1560, 1710, 1820, 1880, 1930, 2000, 2050, 2100, 2140, 2150, 2200]
    # list_objects = []
    # for key, value in dict_objects.items():
    #     for i in range(value):
    #         list_objects.append(int(key))
    n = 6500
    m = 45
    print("Размер полотна: {0}. Количество полотен шириной 1 и длиной {1}: {2}.".format(n*m, n, m))
    print("Список предметов (список заказов):")
    print_line(25, list_objects)
    # print(dict(islice(dict_objects.items(), 0, 7)))
    # print(dict(islice(dict_objects.items(), 7, 13)))
    result = reduction(m, n, list_objects)
    result = list(filter(lambda a: a != 0, result))
    len_result = len(result)
    ost = n*len_result - sum([item for item in result])
    print("Список заполненных площадей каждого полотна:\n")
    print_line(10, result)
    print("Количество полотен, которое потребовалось для раскроя: {0}".format(len_result))
    print("Суммарный остаток после раскроя (отходы): {0}".format(ost))
    print("Процент отходов от использования полотен после раскроя: {0}".format(100*ost/(n*len_result)))
    print("Количество заказов, которые не удалось осуществить: {0}".format(len(list_objects)))
    # print(knapsack(n, list_objects, list_objects))
