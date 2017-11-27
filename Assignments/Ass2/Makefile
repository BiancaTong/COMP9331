RoutingPerformance: RoutingPerformance.o WGraph.o
	gcc -o RoutingPerformance RoutingPerformance.o WGraph.o

RoutingPerformance.o : RoutingPerformance.c WGraph.h
	gcc -Wall -Werror -c RoutingPerformance.c

WGraph.o : WGraph.c WGraph.h
	gcc -Wall -Werror -c WGraph.c

clean:
	rm -f RoutingPerformance RoutingPerformance.o WGraph.o core
