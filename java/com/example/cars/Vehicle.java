// Copyright (C) 2019 Sony Mobile Communications Inc.
// Licensed under the LICENSE

package com.example.cars;

public abstract class Vehicle {
	public final String make;
	public final int nwheels;
	private final short[][] wheelDimensions;

	public Vehicle(String make, short[][] wdims) {
		this.make = make;
		wheelDimensions = wdims;
		nwheels = wdims.length;
	}

	abstract boolean isMotorized();
}
