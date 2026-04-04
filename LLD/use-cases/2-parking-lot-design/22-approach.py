"""
Parking Lot - Low Level Design (Python)
========================================
Covers: Singleton, Strategy (pricing), Abstract Vehicle, Ticket lifecycle,
        floor-level locking for concurrency safety.
"""

from __future__ import annotations

import threading
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional


# ─────────────────────────────────────────────
#  Enums
# ─────────────────────────────────────────────

class VehicleType(Enum):
    CAR        = auto()
    TRUCK      = auto()
    MOTORCYCLE = auto()
    VAN        = auto()


class SlotType(Enum):
    COMPACT    = auto()
    LARGE      = auto()
    MOTORCYCLE = auto()
    HANDICAPPED = auto()


class TicketStatus(Enum):
    ACTIVE = auto()
    PAID   = auto()
    LOST   = auto()


# ─────────────────────────────────────────────
#  Pricing Strategy
# ─────────────────────────────────────────────

class ParkingRate(ABC):
    """Strategy interface for calculating parking fees."""

    @abstractmethod
    def calculate(self, ticket: "Ticket") -> float:
        ...


class HourlyRate(ParkingRate):
    def __init__(self, rate_per_hour: float = 50.0):
        self.rate_per_hour = rate_per_hour

    def calculate(self, ticket: "Ticket") -> float:
        if ticket.exit_time is None:
            raise ValueError("Ticket has no exit time.")
        delta = ticket.exit_time - ticket.entry_time
        hours = max(1, -(-delta.total_seconds() // 3600))  # ceiling division
        return hours * self.rate_per_hour


class DailyRate(ParkingRate):
    def __init__(self, rate_per_day: float = 300.0):
        self.rate_per_day = rate_per_day

    def calculate(self, ticket: "Ticket") -> float:
        if ticket.exit_time is None:
            raise ValueError("Ticket has no exit time.")
        delta = ticket.exit_time - ticket.entry_time
        days = max(1, -(-delta.total_seconds() // 86400))
        return days * self.rate_per_day


class MonthlyRate(ParkingRate):
    def __init__(self, flat_fee: float = 2000.0):
        self.flat_fee = flat_fee

    def calculate(self, ticket: "Ticket") -> float:
        return self.flat_fee


# ─────────────────────────────────────────────
#  Payment
# ─────────────────────────────────────────────

class PaymentMethod(ABC):
    @abstractmethod
    def pay(self, amount: float) -> bool:
        ...


class CashPayment(PaymentMethod):
    def pay(self, amount: float) -> bool:
        print(f"  [Cash] ₹{amount:.2f} received.")
        return True


class CardPayment(PaymentMethod):
    def pay(self, amount: float) -> bool:
        print(f"  [Card] ₹{amount:.2f} charged.")
        return True


class UPIPayment(PaymentMethod):
    def pay(self, amount: float) -> bool:
        print(f"  [UPI]  ₹{amount:.2f} debited.")
        return True


# ─────────────────────────────────────────────
#  Vehicle (Abstract)
# ─────────────────────────────────────────────

class Vehicle(ABC):
    def __init__(self, license_plate: str, vehicle_type: VehicleType):
        self.license_plate = license_plate
        self.vehicle_type  = vehicle_type
        self.ticket: Optional["Ticket"] = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.license_plate})"


class Car(Vehicle):
    def __init__(self, license_plate: str):
        super().__init__(license_plate, VehicleType.CAR)


class Truck(Vehicle):
    def __init__(self, license_plate: str):
        super().__init__(license_plate, VehicleType.TRUCK)


class Motorcycle(Vehicle):
    def __init__(self, license_plate: str):
        super().__init__(license_plate, VehicleType.MOTORCYCLE)


class Van(Vehicle):
    def __init__(self, license_plate: str):
        super().__init__(license_plate, VehicleType.VAN)


# ─────────────────────────────────────────────
#  Ticket
# ─────────────────────────────────────────────

class Ticket:
    def __init__(self, vehicle: Vehicle, slot: "ParkingSlot"):
        self.ticket_id   = str(uuid.uuid4())[:8].upper()
        self.vehicle     = vehicle
        self.slot        = slot
        self.entry_time  = datetime.now()
        self.exit_time:  Optional[datetime] = None
        self.status      = TicketStatus.ACTIVE

    def close(self) -> None:
        self.exit_time = datetime.now()
        self.status    = TicketStatus.PAID

    def __repr__(self) -> str:
        return (
            f"Ticket[{self.ticket_id}] {self.vehicle.license_plate} "
            f"@ slot {self.slot.slot_number} | {self.status.name}"
        )


# ─────────────────────────────────────────────
#  Parking Slot
# ─────────────────────────────────────────────

# Which vehicle types are allowed in each slot type
SLOT_VEHICLE_COMPATIBILITY: Dict[SlotType, List[VehicleType]] = {
    SlotType.COMPACT:     [VehicleType.CAR, VehicleType.VAN],
    SlotType.LARGE:       [VehicleType.TRUCK, VehicleType.VAN, VehicleType.CAR],
    SlotType.MOTORCYCLE:  [VehicleType.MOTORCYCLE],
    SlotType.HANDICAPPED: [VehicleType.CAR, VehicleType.VAN],
}


class ParkingSlot:
    def __init__(self, slot_number: str, slot_type: SlotType):
        self.slot_number = slot_number
        self.slot_type   = slot_type
        self.is_free     = True
        self.vehicle: Optional[Vehicle] = None

    def can_fit(self, vehicle: Vehicle) -> bool:
        return vehicle.vehicle_type in SLOT_VEHICLE_COMPATIBILITY[self.slot_type]

    def assign_vehicle(self, vehicle: Vehicle) -> None:
        # is_free is already set to False by get_free_slot() inside the floor lock.
        # We only set it here if called directly (e.g. in tests).
        self.vehicle = vehicle
        self.is_free = False

    def remove_vehicle(self) -> None:
        self.vehicle = None
        self.is_free = True

    def __repr__(self) -> str:
        state = "FREE" if self.is_free else f"OCC({self.vehicle.license_plate})"
        return f"Slot[{self.slot_number} {self.slot_type.name} {state}]"


# ─────────────────────────────────────────────
#  Display Board
# ─────────────────────────────────────────────

class DisplayBoard:
    def __init__(self, floor_number: int):
        self.floor_number = floor_number
        self.free_counts: Dict[SlotType, int] = {t: 0 for t in SlotType}

    def update(self, slots_by_type: Dict[SlotType, List[ParkingSlot]]) -> None:
        for slot_type, slots in slots_by_type.items():
            self.free_counts[slot_type] = sum(1 for s in slots if s.is_free)

    def show(self) -> None:
        print(f"\n  ── Floor {self.floor_number} Display Board ──")
        for t, count in self.free_counts.items():
            print(f"     {t.name:<12}: {count} free")


# ─────────────────────────────────────────────
#  Parking Floor
# ─────────────────────────────────────────────

class ParkingFloor:
    def __init__(self, floor_number: int):
        self.floor_number = floor_number
        self.slots_by_type: Dict[SlotType, List[ParkingSlot]] = {t: [] for t in SlotType}
        self.display_board = DisplayBoard(floor_number)
        self._lock = threading.Lock()  # floor-level lock for concurrency

    def add_slot(self, slot: ParkingSlot) -> None:
        self.slots_by_type[slot.slot_type].append(slot)
        self.display_board.update(self.slots_by_type)

    def get_free_slot(self, vehicle: Vehicle) -> Optional[ParkingSlot]:
        """Thread-safe: find and tentatively mark a slot as occupied."""
        with self._lock:
            for slot_type, slots in self.slots_by_type.items():
                for slot in slots:
                    if slot.is_free and slot.can_fit(vehicle):
                        slot.is_free = False   # reserve immediately inside lock
                        return slot
        return None

    def free_slot(self, slot: ParkingSlot) -> None:
        slot.remove_vehicle()
        self.display_board.update(self.slots_by_type)

    def free_slot_count(self) -> int:
        return sum(s.is_free for slots in self.slots_by_type.values() for s in slots)

    def show_board(self) -> None:
        self.display_board.update(self.slots_by_type)
        self.display_board.show()


# ─────────────────────────────────────────────
#  Entrance / Exit Panels
# ─────────────────────────────────────────────

class EntrancePanel:
    def __init__(self, panel_id: str, parking_lot: "ParkingLot"):
        self.panel_id   = panel_id
        self.parking_lot = parking_lot

    def scan_and_issue_ticket(self, vehicle: Vehicle) -> Optional[Ticket]:
        return self.parking_lot.get_new_ticket(vehicle)


class ExitPanel:
    def __init__(self, panel_id: str, parking_lot: "ParkingLot",
                 rate: ParkingRate, payment_method: PaymentMethod):
        self.panel_id       = panel_id
        self.parking_lot    = parking_lot
        self.rate           = rate
        self.payment_method = payment_method

    def process_exit(self, ticket: Ticket) -> float:
        return self.parking_lot.process_exit(ticket, self.rate, self.payment_method)


# ─────────────────────────────────────────────
#  ParkingLot — Singleton
# ─────────────────────────────────────────────

class ParkingLot:
    _instance: Optional["ParkingLot"] = None
    _init_lock = threading.Lock()

    def __new__(cls) -> "ParkingLot":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Guard against re-initialisation on subsequent calls to __init__
        if hasattr(self, "_initialised"):
            return
        self._initialised = True

        self.name    = "City Center Parking"
        self.address = "MG Road, Bengaluru"
        self.floors:  List[ParkingFloor] = []
        self.active_tickets: Dict[str, Ticket] = {}  # ticket_id → Ticket
        self._revenue = 0.0

    # ── Floor management ──────────────────────

    def add_floor(self, floor: ParkingFloor) -> None:
        self.floors.append(floor)

    # ── Ticket issuance ───────────────────────

    def get_new_ticket(self, vehicle: Vehicle) -> Optional[Ticket]:
        slot = self._find_slot(vehicle)
        if slot is None:
            print(f"  [FULL] No suitable slot for {vehicle}")
            return None

        slot.assign_vehicle(vehicle)
        ticket = Ticket(vehicle, slot)
        vehicle.ticket = ticket
        self.active_tickets[ticket.ticket_id] = ticket
        print(f"  [ENTRY] {vehicle} → {slot.slot_number}  Ticket: {ticket.ticket_id}")
        return ticket

    def _find_slot(self, vehicle: Vehicle) -> Optional[ParkingSlot]:
        for floor in self.floors:
            slot = floor.get_free_slot(vehicle)
            if slot:
                return slot
        return None

    # ── Exit & payment ────────────────────────

    def process_exit(self, ticket: Ticket,
                     rate: ParkingRate,
                     payment: PaymentMethod) -> float:
        if ticket.status != TicketStatus.ACTIVE:
            print(f"  [WARN] Ticket {ticket.ticket_id} is not active.")
            return 0.0

        ticket.close()
        fee = rate.calculate(ticket)
        payment.pay(fee)

        # Free the slot on the correct floor
        for floor in self.floors:
            if ticket.slot in [s for slots in floor.slots_by_type.values() for s in slots]:
                floor.free_slot(ticket.slot)
                break

        del self.active_tickets[ticket.ticket_id]
        self._revenue += fee
        print(f"  [EXIT]  {ticket.vehicle} | fee ₹{fee:.2f} | Ticket {ticket.ticket_id} PAID")
        return fee

    # ── Queries ───────────────────────────────

    def is_full(self, vehicle_type: Optional[VehicleType] = None) -> bool:
        return all(floor.free_slot_count() == 0 for floor in self.floors)

    def total_revenue(self) -> float:
        return self._revenue

    def show_status(self) -> None:
        print(f"\n{'═'*40}")
        print(f"  {self.name}")
        print(f"  {self.address}")
        print(f"  Revenue collected: ₹{self._revenue:.2f}")
        for floor in self.floors:
            floor.show_board()
        print(f"{'═'*40}\n")


# ─────────────────────────────────────────────
#  Factory helpers
# ─────────────────────────────────────────────

def build_default_lot() -> ParkingLot:
    """
    Creates a 2-floor lot:
      Floor 1 — 4 compact, 2 large, 2 motorcycle, 1 handicapped
      Floor 2 — 4 compact, 2 large, 2 motorcycle
    """
    lot = ParkingLot()

    for floor_num in (1, 2):
        floor = ParkingFloor(floor_num)

        for i in range(1, 5):
            floor.add_slot(ParkingSlot(f"F{floor_num}C{i}", SlotType.COMPACT))
        for i in range(1, 3):
            floor.add_slot(ParkingSlot(f"F{floor_num}L{i}", SlotType.LARGE))
        for i in range(1, 3):
            floor.add_slot(ParkingSlot(f"F{floor_num}M{i}", SlotType.MOTORCYCLE))
        if floor_num == 1:
            floor.add_slot(ParkingSlot(f"F{floor_num}H1", SlotType.HANDICAPPED))

        lot.add_floor(floor)

    return lot


# ─────────────────────────────────────────────
#  Demo / Driver
# ─────────────────────────────────────────────

def demo() -> None:
    lot = build_default_lot()
    lot.show_status()

    entrance = EntrancePanel("E1", lot)
    exit_gate = ExitPanel("X1", lot, HourlyRate(rate_per_hour=50), CashPayment())

    print("── Vehicles entering ──")
    car1  = Car("KA01AB1234")
    car2  = Car("KA02CD5678")
    bike1 = Motorcycle("KA03EF9999")
    truck = Truck("MH04GH1111")

    t1 = entrance.scan_and_issue_ticket(car1)
    t2 = entrance.scan_and_issue_ticket(car2)
    t3 = entrance.scan_and_issue_ticket(bike1)
    t4 = entrance.scan_and_issue_ticket(truck)

    lot.show_status()

    print("── Vehicles exiting ──")
    if t1:
        exit_gate.process_exit(t1)
    if t3:
        # Motorcycle pays by UPI
        upi_exit = ExitPanel("X2", lot, HourlyRate(30), UPIPayment())
        upi_exit.process_exit(t3)

    lot.show_status()

    # Singleton check
    lot2 = ParkingLot()
    assert lot is lot2, "Singleton violated!"
    print("  [OK] Singleton verified — lot is lot2")


if __name__ == "__main__":
    demo()