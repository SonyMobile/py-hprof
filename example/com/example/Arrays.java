// Copyright (C) 2019 Snild Dolkow
// Licensed under the LICENSE.

package com.example;

public class Arrays {
	final int[] i1 = new int[] {1, 2, 3};
	final int[][] i2 = new int[2][2];

	final char[] c1 = new char[] { 'h', 'e', 'l', 'l', 'o' };
	final char[][] c2 = new char[2][];

	public Arrays() {
		i2[0][0] = 10;
		i2[0][1] = 15;
		i2[1][0] = 13;
		i2[1][1] = 11;

		c2[0] = c1;
		c2[1] = new char[] {'w', 'o', 'r', 'l', 'd'};
	}
}
