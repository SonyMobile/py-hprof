// Copyright (C) 2019 Snild Dolkow
// Licensed under the LICENSE.

package com.example.cars;

public abstract class Vehicle {
	protected final String make;
	protected final int numWheels;

	public Vehicle(String make, int numWheels) {
		this.make = make;
		this.numWheels = numWheels;
	}
}
