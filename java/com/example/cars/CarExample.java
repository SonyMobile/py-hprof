package com.example.cars;

public class CarExample {
	private static Object bikeSuper;
	private static String nothing = "not yet nothing";
	private Object[] objs;

	static {
		nothing = null;
	}

	public CarExample() {
		objs = new Object[] {
			new Car("Lolvo"),
			new Car("Yotoya"),
			new Bike("Fånark"),
			new Limo(),
			new Bike("Descent")
		};
		bikeSuper = objs[4].getClass();
	}
}
