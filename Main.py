import csv
import sys
import os
import uuid
from collections import defaultdict



PRICE_PER_STATION = 8

class stations:
    # Station class to represent a single station.
    def __init__(self, station_id, station_name,line_id,line_name,position):
        self.station_id = station_id
        self.station_name = station_name
        self.line_id = line_id
        self.line_name = line_name
        self.position = position

class lines:
    # Line class to represent a single metro line.
    def __init__(self, line_id, line_name):
        self.line_id = line_id
        self.line_name = line_name
    
class tickets:
    # Ticket class to represent a single purchased ticket.
    def __init__(self, ticket_id, origin, destination, price, path_list,instructions):
        self.ticket_id = ticket_id
        self.origin = origin
        self.destination = destination
        self.price = price
        self.path_list = path_list
        self.instructions = instructions

    def to_csv_row(self):
        priceNEW=str(round(self.price,2))
        path_str= self.path_list[0]
        for i in range(1,len(self.path_list)):
            path_str= path_str + "->"+ self.path_list[i]

        instructions_str=""
        if self.instructions:
            instructions_str= self.instructions[0]
            for i in range(1,len(self.instructions)):
                instructions_str= instructions_str + " | "+ self.instructions[i]
        return [self.ticket_id, self.origin, self.destination, priceNEW,path_str, instructions_str]

    def from_csv_row(row):
        instructions = []
        if row[5]:
            instructions = row[5].split(" | ")
        else:
            instructions = ['No line changes required.']
        return tickets(ticket_id=row[0],
                       origin=row[1]
                       ,destination=row[2]
                       ,price=float(row[3]),
                       path_list=row[4].split(";"),
                       instructions=instructions)

    def display(self):
        print(f"\nTicket ID: {self.ticket_id}")
        print(f"route: {self.origin} to {self.destination}")
        price_str = str(round(self.price, 2))
        print(f"Fare: ₹{price_str}")
        stops = len(self.path_list) - 1
        print("stops crossed:  " + str(stops))
        if self.instructions != ['No line changes required.']:
            print(" Travel Instructions:\n")
            for step in self.instructions:
                print(f" - {step}")
        else:
            print("No line changes required.")

        path_display = self.path_list[0]
        for i in range(1, len(self.path_list)):
            path_display = path_display+ " -> " + self.path_list[i]
        
        print(f"Full path of the Journey: {path_display}\n")


class MetroSystem:
    def __init__(self):
        self.station_id_to_names = {}
        self.line_id_to_names = {}
        self.line_to_stations = defaultdict(list)
        self.metro_graph = defaultdict(list)
        self.station_to_lines = defaultdict(set)
        self.purchased_tickets = []
        self.data()
        self.build_network_graph()
        self.load_tickets_from_file()

    def data(self):
        try:
            # Use DictReader and normalize header keys to lowercase to allow case-insensitive access
            with open('stations.csv', 'r', newline='') as stations_data:
                station_reader = csv.DictReader(stations_data)
                for row in station_reader:
                    # normalize keys to lowercase to avoid header-casing issues
                    row_lower = {k.strip().lower(): v for k, v in row.items()}
                    sid = row_lower.get('station_id')
                    sname = row_lower.get('station_name')
                    if sid and sname:
                        self.station_id_to_names[sid] = sname

            with open('lines.csv', 'r', newline='') as lines_data:
                line_reader = csv.DictReader(lines_data)
                for row in line_reader:
                    row_lower = {k.strip().lower(): v for k, v in row.items()}
                    lid = row_lower.get('line_id')
                    lname = row_lower.get('line_name')
                    if lid and lname:
                        self.line_id_to_names[lid] = lname

            station_positions = defaultdict(lambda: defaultdict(int))
            with open('LINE_STATIONS.csv', 'r', newline='') as line_station_data:
                line_station_reader = csv.DictReader(line_station_data)
                for row in line_station_reader:
                    row_lower = {k.strip().lower(): v for k, v in row.items()}
                    line_id = row_lower.get('line_id')
                    station_id = row_lower.get('station_id')
                    pos = row_lower.get('position')
                    if not (line_id and station_id and pos):
                        continue
                    try:
                        position = int(pos)
                    except ValueError:
                        continue
                    station_positions[line_id][station_id] = position

            for line_id, stations in station_positions.items():
                line_name = self.line_id_to_names.get(line_id)
                if not line_name:
                    continue
            
                sorted_stations = sorted(stations.items(), key=lambda x: x[1])
                order_names= []
                for s_id, _ in sorted_stations:
                    s_name = self.station_id_to_names.get(s_id)
                    if s_name:
                        order_names.append(s_name)
                        self.station_to_lines[s_name].add(line_name)
                self.line_to_stations[line_name].extend(order_names)
            # summary of loaded data
            print("loaded " + str(len(self.line_id_to_names)) + " lines and " + str(len(self.station_id_to_names)) + " stations.")
        except FileNotFoundError as e:
            print("Error: One or more data files are missing." + e.filename)
            sys.exit(1)
        


    def build_network_graph(self):
        for line_name, stations in self.line_to_stations.items():
            for station in stations:
                self.station_to_lines[station].add(line_name)
            for i in range(len(stations) - 1):
                u=stations[i]
                v=stations[i+1]
                self.metro_graph[u].append((v, line_name))
                self.metro_graph[v].append((u, line_name))
        print("Metro network graph built with " + str(len(self.metro_graph)) + " stations.")

    
    def load_tickets_from_file(self):
        if not os.path.exists('tickets.csv'):
            self.save_tickets_to_file(initial=True)
            return
        try:
            with open('tickets.csv', 'r') as tickets_data:
                ticket_reader = csv.reader(tickets_data)
                next(ticket_reader, None)
                for row in ticket_reader:
                    if len(row) == 6:
                        ticket = tickets.from_csv_row(row)
                        self.purchased_tickets.append(ticket)
            print("Loaded " + str(len(self.purchased_tickets)) + " purchased tickets from file.")
        except Exception:
            print("Warning: Could not load tickets from file. Starting with an empty ticket list.")
            self.saved_tickets_to_file(initial=True)


    def save_tickets_to_file(self, initial=False):
        with open('tickets.csv', mode='w', newline='') as tickets_data:
            ticket_writer = csv.writer(tickets_data)
            ticket_writer.writerow(['ticket_id', 'origin', 'destination', 'price', 'path_list','instructions'])
            if not initial and self.purchased_tickets:
                for ticket in self.purchased_tickets:
                    ticket_writer.writerow(ticket.to_csv_row())
        if not initial:
            print("Saved " + str(len(self.purchased_tickets)) + " purchased tickets to file.")

    
    def bfs_shortest_path(self, start_station, end_station):
        queue = ([(start_station, [start_station])])
        visited = {start_station}
        while queue:
            current_station, path = queue.popleft()
            if current_station == end_station:
                stations_crossed = len(path) - 1
                return path, stations_crossed
            for neighbor, line_name in self.metro_graph.get(current_station, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append((neighbor, new_path))
        return None, 0

    def get_segment_line(self, station1, station2):
        for neighbor, line_name in self.metro_graph.get(station1, []):
            if neighbor == station2:
                return line_name
        return None


    def generate_instructons(self, path):
        if len(path) <= 1:
            return ['No Path Found Or Already At Destination.']
        instructions = []
        current_line = self.get_segment_line(path[0], path[1])
        start_station = path[0]
        for i in range(1, len(path)):
            current_station = path[i-1]
            next_station = path[i]
            segment_line = self.get_segment_line(current_station, next_station)
            if segment_line and segment_line != current_line:
                instructions.append(f"Take {current_line} from {start_station} to {current_station}.")
                instructions.append(f"Change line at {current_station} to {segment_line}.")
                current_line = segment_line
                start_station = current_station
            final_instruction = f"Take {current_line} from {start_station} to your final destination {path[-1]}."
            instructions.append(final_instruction)
            if len(instructions) == 1 and instructions[0].startswith("Take the"): return ['No line changes required.']
            return instructions
        
    
    def display_stations(self):
        print("\nAvailable Metro Stations:")
        transfer_stations = {s for s, lines in self.station_to_lines.items() if len(lines) > 1}
        for line_name, stations in self.line_to_stations.items():
            stations_with_status = []
            for name in stations:
                status=""
                if name in transfer_stations:
                    status=" (Transfer Station)"
                stations_with_status.append(name + status)
            print(f"\nLine: {line_name}")
            station_list_str = stations_with_status[0]
            for i in range(1, len(stations_with_status)):
                station_list_str = station_list_str + " , " + stations_with_status[i]
            print("  " + station_list_str)
        


    def purchase_ticket(self, origin, destination):
        if origin == destination:
            print("Origin and destination stations cannot be the same.")
            return
        if origin not in self.metro_graph or destination not in self.metro_graph:
            print("One or both of the specified stations do not exist in the metro system.")
            return
        path, stops  = self.bfs_shortest_path(origin, destination)
        if not path or stops == 0:
            print("No path found between the specified stations.")
            return
        fare = stops * PRICE_PER_STATION
        instructions = self.generate_instructons(path)
        ticket_id = str(uuid.uuid4())[:8]
        new_ticket = tickets(ticket_id, origin, destination, fare, path, instructions)
        self.purchased_tickets.append(new_ticket)
        self.save_tickets_to_file()
        print("\nTicket purchased successfully!")
        new_ticket.display()

    def desplay_tickets(self):
        if not self.purchased_tickets:
            print("No tickets have been purchased yet.")
            return
        print("\nYour Purchased Tickets: ")
        for ticket in self.purchased_tickets:
            ticket.display()

    def run(self):
        while True:
            print("\nMetro Ticketing System")
            print("1. View All Metro Stations")
            print("2. Purchase A New Ticket")
            print("3. View Purchased Tickets")
            print("4. Exit")
            choice = input("Enter your choice (1-4): ")
            if choice == '1':
                self.display_stations()
            elif choice == '2':
                origin = input("Enter origin station: ")
                destination = input("Enter destination station: ").strip()
                self.purchase_ticket(origin, destination)
            elif choice == '3':
                self.desplay_tickets()
            elif choice == '4':
                self.save_tickets_to_file()
                print("Thankyou for using our service.\nExiting Metro Ticketing System. Goodbye!")
                break
            else:
                print("Invalid choice. Please Enter a number between 1 and 4.")

if __name__ == "__main__":
    print("Initializing Metro Ticketing System...")
    metro_system = MetroSystem()
    metro_system.run()
