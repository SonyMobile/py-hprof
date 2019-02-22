package com.example;

public class Car extends Vehicle {
	public static final int MAX_REASONABLE_WHEEL_COUNT = 8;

	public Car(String make) {
		super(make, mkdims());
	}

	private static short[][] mkdims() {
		short[][] dims = new short[4][];
		for (int i=0; i<4; ++i) {
			dims[i] = new short[] {50, 10};
		}
		return dims;
	}

	boolean isMotorized() {
		return true;
	}
}
