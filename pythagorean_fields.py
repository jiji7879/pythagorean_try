def square_mod_list(prime):
    mod_list = []
    unique_mods = set()
    for i in range(prime):
        mod = (i * i) % prime
        if mod < prime // 2:
            mod_list.append(mod)
            unique_mods.add(mod)
        else:
            mod_list.append(mod - prime)
    print("Prime:", prime)
    print(len(unique_mods), "unique mods:", sorted(unique_mods))
    return mod_list


if __name__ == "__main__":
    prime = 59
    mods = square_mod_list(prime)
    for i in range(len(mods)):
        print(f"{i}^2 mod {prime} = {mods[i]}")