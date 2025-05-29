import tkinter as tk

root = tk.Tk()
root.title("Test")

frame = tk.Frame(root)
frame.pack(expand=True, fill="both")

for i in range(3):
    frame.rowconfigure(i, weight=1)
    frame.columnconfigure(i, weight=1)
    for j in range(3):
        btn = tk.Button(frame, text=f"{i},{j}", width=10, height=5)
        btn.grid(row=i, column=j, sticky="nsew")

root.mainloop()
