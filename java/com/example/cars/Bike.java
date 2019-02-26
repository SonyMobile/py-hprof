package com.example.cars;

public class Bike extends Vehicle {
	public Bike(String make) {
		super(make, new short[][] {
			new short[] { 100, 1 },
			new short[] { 5,   1 } // it's one of those old-timey bikes with one really big wheel.
		});
	}

	boolean isMotorized() {
		return false;
	}
}
