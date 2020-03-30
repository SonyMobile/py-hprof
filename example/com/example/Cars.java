// Copyright (C) 2019 Snild Dolkow
// Licensed under the LICENSE.

package com.example;

import com.example.cars.*;

public class Cars {
	Vehicle[] vehicles;
	Car swe, jap;
	Limo generic;
	Bike mine, redYellow;

	public Cars() {
		swe = new Car("Lolvo");
		jap = new Car("Toy Yoda");
		generic = new Limo();
		mine = new Bike("Fånark");
		redYellow = new Bike("Axes");
		vehicles = new Vehicle[] { swe, jap, generic, mine, redYellow };
	}
}
