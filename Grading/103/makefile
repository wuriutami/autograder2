all: hello.exe

hello.exe: hello.o
	 gcc -o hello.exe hello.o

hello.o: hello.cpp
	 gcc -c hello.cpp
     
clean:
	 rm hello.o hello.exe